"""Tests for Lab 02 - Prompt chaining.

The gate and the chain control flow are deterministic. The model-backed steps
are stubbed out, so every test runs offline and no API key is needed.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


def _load(name: str, path: Path):
    """Load a module by file path.

    The module is registered in sys.modules before execution because
    dataclasses look their own module up by name while being created.
    """
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


LAB_ROOT = Path(__file__).resolve().parents[1]
solution = _load("lab02_solution", LAB_ROOT / "solution" / "main.py")

# A list that clears the gate: every entry is specific and long enough to act on.
GOOD_REQUIREMENTS = [
    "The page must load in under two seconds on a slow connection.",
    "Customers can request an email update when the order is late.",
    "The layout must work on phone-sized screens.",
]


def test_gate_rejects_an_empty_requirement_list():
    """An empty extraction fails the gate with a reason that says so."""
    ok, reason = solution.gate_requirements([])
    assert ok is False
    assert "nothing was extracted" in reason


def test_gate_rejects_a_single_vague_requirement():
    """A requirement too short to act on fails the gate."""
    ok, reason = solution.gate_requirements(["make it good"])
    assert ok is False
    assert "make it good" in reason


def test_gate_accepts_a_well_formed_list():
    """Specific, actionable requirements pass."""
    ok, reason = solution.gate_requirements(GOOD_REQUIREMENTS)
    assert ok is True
    assert str(len(GOOD_REQUIREMENTS)) in reason


def test_run_chain_returns_every_intermediate_output(monkeypatch):
    """The result carries requirements, draft, and final for inspection."""
    monkeypatch.setattr(
        solution, "extract_requirements", lambda brief: list(GOOD_REQUIREMENTS)
    )
    monkeypatch.setattr(solution, "draft_spec", lambda requirements: "the draft")
    monkeypatch.setattr(solution, "polish_spec", lambda draft: "the final")

    result = solution.run_chain("a brief")
    assert result["requirements"] == GOOD_REQUIREMENTS
    assert result["draft"] == "the draft"
    assert result["final"] == "the final"
    assert result["stopped_at"] is None


def test_run_chain_stops_when_the_gate_fails(monkeypatch):
    """A failed gate names itself in stopped_at and draft_spec never runs."""
    monkeypatch.setattr(solution, "extract_requirements", lambda brief: ["vague"])

    def draft_must_not_run(requirements):
        raise AssertionError("draft_spec ran after a failed gate")

    monkeypatch.setattr(solution, "draft_spec", draft_must_not_run)

    result = solution.run_chain("a brief", max_retries=0)
    assert result["stopped_at"] == "gate_requirements"
    assert result["gate"][0] is False
    assert result["draft"] == ""


def test_run_chain_retries_the_failed_step_once(monkeypatch):
    """Only the failed step is retried: two extractions, one draft."""
    calls: list[str] = []

    def extract(brief):
        calls.append(brief)
        # First attempt fails the gate, second succeeds.
        return [] if len(calls) == 1 else list(GOOD_REQUIREMENTS)

    monkeypatch.setattr(solution, "extract_requirements", extract)
    monkeypatch.setattr(solution, "draft_spec", lambda requirements: "draft")
    monkeypatch.setattr(solution, "polish_spec", lambda draft: "final")

    result = solution.run_chain("a brief", max_retries=1)
    assert len(calls) == 2
    assert result["stopped_at"] is None
    assert result["final"] == "final"
