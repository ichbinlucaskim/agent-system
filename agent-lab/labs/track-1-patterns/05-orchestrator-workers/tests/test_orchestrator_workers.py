"""Tests for Lab 05 - Orchestrator and workers.

Plan validation is pure logic, and the orchestration control flow is tested
offline by stubbing the model calls, so no test needs an API key.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import SimpleNamespace


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
solution = _load("lab05_solution", LAB_ROOT / "solution" / "main.py")


def _fake_response(text: str):
    """Build the minimal response shape that text_of understands."""
    return SimpleNamespace(content=[SimpleNamespace(type="text", text=text)])


def test_validate_plan_drops_entries_missing_required_fields():
    """A subtask without a description never reaches a worker."""
    plan = [
        {"id": "t1"},
        {"id": "t2", "description": "Check shipping rules for the EU."},
        {"description": "An entry with no id."},
        "not even a dict",
    ]
    valid = solution.validate_plan(plan)
    assert [entry["id"] for entry in valid] == ["t2"]


def test_validate_plan_caps_the_subtask_count():
    """A twenty entry plan is truncated to max_subtasks."""
    plan = [
        {"id": f"t{index}", "description": f"Subtask number {index}."}
        for index in range(20)
    ]
    assert len(solution.validate_plan(plan, max_subtasks=6)) == 6


def test_validate_plan_removes_duplicate_subtasks():
    """Identical descriptions collapse to one entry."""
    plan = [
        {"id": "t1", "description": "Check VAT registration thresholds."},
        {"id": "t2", "description": "check vat  registration thresholds."},
        {"id": "t3", "description": "Summarize the returns directive."},
    ]
    valid = solution.validate_plan(plan)
    assert [entry["id"] for entry in valid] == ["t1", "t3"]


def test_orchestrate_returns_the_plan_with_the_answer(monkeypatch):
    """The plan rides along with the answer, so the run is explainable."""
    fixed = [{"id": "t1", "description": "Check shipping rules for the EU."}]
    monkeypatch.setattr(solution, "plan", lambda task: [dict(fixed[0])])
    monkeypatch.setattr(
        solution,
        "run_worker",
        lambda subtask, context: {"id": subtask["id"], "result": "found", "error": None},
    )
    monkeypatch.setattr(solution, "synthesize", lambda task, results: "the answer")

    outcome = solution.orchestrate("the task")
    assert outcome["plan"] == fixed
    assert outcome["answer"] == "the answer"
    assert outcome["results"][0]["result"] == "found"


def test_a_failing_worker_does_not_abort_the_run(monkeypatch):
    """One worker raising leaves an error entry while synthesis still runs."""
    fixed = [
        {"id": "t1", "description": "explode on purpose"},
        {"id": "t2", "description": "Summarize the returns directive."},
    ]
    monkeypatch.setattr(solution, "plan", lambda task: fixed)

    def fake_complete(messages, *, system=None, **kwargs):
        # The worker for t1 raises inside its model call; every other call,
        # including synthesis, succeeds.
        if "explode on purpose" in messages[0]["content"]:
            raise RuntimeError("boom")
        return _fake_response("ok")

    monkeypatch.setattr(solution, "complete", fake_complete)

    outcome = solution.orchestrate("the task")
    by_id = {entry["id"]: entry for entry in outcome["results"]}
    assert by_id["t1"]["result"] is None
    assert "boom" in by_id["t1"]["error"]
    assert by_id["t2"]["error"] is None
    assert outcome["answer"] == "ok"
