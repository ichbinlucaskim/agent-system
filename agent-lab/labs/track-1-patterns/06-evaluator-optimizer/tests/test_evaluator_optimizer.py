"""Tests for Lab 06 - Evaluator and optimizer.

The two loop exits and the refinement bookkeeping are deterministic once
generate and evaluate are stubbed, so every test runs offline and no API key
is needed.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from typing import Any


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
solution = _load("lab06_solution", LAB_ROOT / "solution" / "main.py")


def _stub_loop(monkeypatch, scores: list[int], feedbacks: list[str] | None = None):
    """Drive refine with scripted drafts and evaluations.

    Returns the list of (task, feedback) pairs generate was called with, so
    tests can check what the next iteration actually saw.
    """
    generate_calls: list[tuple[str, str | None]] = []
    state = {"index": 0}

    def fake_generate(task: str, feedback: str | None = None) -> str:
        generate_calls.append((task, feedback))
        return f"draft {len(generate_calls)}"

    def fake_evaluate(task: str, draft: str) -> dict[str, Any]:
        index = state["index"]
        state["index"] += 1
        feedback = feedbacks[index] if feedbacks else f"feedback {index + 1}"
        return {"score": scores[index], "passed": False, "feedback": feedback}

    monkeypatch.setattr(solution, "generate", fake_generate)
    monkeypatch.setattr(solution, "evaluate", fake_evaluate)
    return generate_calls


def test_is_done_stops_on_a_passing_score():
    """A score at or above the target exits with a success reason."""
    done, reason = solution.is_done(
        {"score": 9}, 1, max_iterations=3, target_score=8
    )
    assert done is True
    assert "success" in reason


def test_is_done_stops_at_the_iteration_budget():
    """The loop stops at max_iterations even when nothing ever passed."""
    done, reason = solution.is_done(
        {"score": 2}, 3, max_iterations=3, target_score=8
    )
    assert done is True
    assert "exhausted" in reason

    # Below the budget with a failing score, the loop keeps going.
    done, _ = solution.is_done({"score": 2}, 1, max_iterations=3, target_score=8)
    assert done is False


def test_refine_returns_the_best_draft_not_the_last(monkeypatch):
    """Scores of 5, 9, 6 return the draft that scored 9."""
    _stub_loop(monkeypatch, scores=[5, 9, 6])
    outcome = solution.refine("the task", max_iterations=3, target_score=10)
    assert outcome["draft"] == "draft 2"
    assert outcome["score"] == 9
    assert outcome["iteration"] == 2


def test_refine_threads_feedback_into_the_next_generation(monkeypatch):
    """The second generate call receives the first evaluation's critique."""
    generate_calls = _stub_loop(
        monkeypatch, scores=[3, 9], feedbacks=["shorten the opening", "none"]
    )
    solution.refine("the task", max_iterations=3, target_score=8)
    assert generate_calls[0][1] is None
    assert generate_calls[1][1] == "shorten the opening"


def test_refine_records_the_score_history(monkeypatch):
    """One history entry per iteration makes a plateau visible afterwards."""
    _stub_loop(monkeypatch, scores=[4, 4, 4])
    outcome = solution.refine("the task", max_iterations=3, target_score=8)
    assert [entry["iteration"] for entry in outcome["history"]] == [1, 2, 3]
    assert [entry["score"] for entry in outcome["history"]] == [4, 4, 4]
    assert "exhausted" in outcome["stop_reason"]
