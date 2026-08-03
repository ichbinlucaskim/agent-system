"""Tests for Lab 14 - Human in the loop.

Classification, the diff, and the enforcement paths are deterministic and
approvals come through a scripted callback, so every test runs offline
without an API key.
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
solution = _load("lab14_solution", LAB_ROOT / "solution" / "main.py")


def test_a_forbidden_action_is_never_executed(monkeypatch):
    """Forbidden is refused before the approver or any executor is reached."""
    executed: list[dict] = []
    prompts: list[str] = []

    def recorder(arguments):
        executed.append(arguments)
        return "dropped"

    def approver(prompt):
        prompts.append(prompt)
        return True

    # Even with an executor registered and an approver saying yes, the
    # refusal must happen first.
    monkeypatch.setitem(solution.EXECUTORS, "delete_database", recorder)
    record = solution.guarded_execute(
        {"name": "delete_database", "arguments": {"env": "production"}}, approver
    )
    assert record["executed"] is False
    assert record["classification"] == "forbidden"
    assert executed == []
    assert prompts == []


def test_an_unknown_tool_defaults_to_confirm():
    """A tool nobody classified is a tool nobody thought about."""
    assert solution.classify_action("format_disk", {}) == "confirm"


def test_an_auto_action_runs_without_an_approver():
    """An auto action executes even when the approver would deny it."""
    prompts: list[str] = []

    def deny(prompt):
        prompts.append(prompt)
        return False

    record = solution.guarded_execute(
        {"name": "read_file", "arguments": {"path": "notes.txt"}}, deny
    )
    assert record["executed"] is True
    assert record["classification"] == "auto"
    assert prompts == []


def test_a_denied_confirmation_does_not_execute():
    """An approver saying no leaves the action unexecuted, with the reason."""

    def deny(prompt):
        return False

    record = solution.guarded_execute(
        {
            "name": "send_email",
            "arguments": {"to": "team@example.com", "subject": "Weekly report"},
        },
        deny,
    )
    assert record["executed"] is False
    assert record["classification"] == "confirm"
    assert "denied" in record["reason"]
    assert record["result"] is None


def test_the_diff_shows_added_and_removed_lines():
    """The approver sees the consequence: what leaves and what arrives."""
    diff = solution.render_diff(
        "alpha\nbeta\ngamma\n", "alpha\nBETA\ngamma\n", "notes.txt"
    )
    assert "-beta" in diff
    assert "+BETA" in diff


def test_every_path_returns_an_audit_record():
    """Refusal, auto, approval, and denial all name their classification."""

    def approve(prompt):
        return True

    def deny(prompt):
        return False

    records = [
        solution.guarded_execute(
            {"name": "delete_database", "arguments": {}}, approve
        ),
        solution.guarded_execute({"name": "list_files", "arguments": {}}, deny),
        solution.guarded_execute(
            {"name": "send_email", "arguments": {"to": "a@example.com"}}, approve
        ),
        solution.guarded_execute(
            {"name": "send_email", "arguments": {"to": "a@example.com"}}, deny
        ),
    ]
    classifications = [record["classification"] for record in records]
    assert classifications == ["forbidden", "auto", "confirm", "confirm"]
    for record in records:
        assert set(record) >= {"executed", "classification", "reason", "result"}
        assert record["reason"]
