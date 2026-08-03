"""Tests for Lab 03 - Routing.

The closed label set, the fallback, dispatch, and the misroute arithmetic are
deterministic once the classifier call is stubbed, so every test runs offline
and no API key is needed.
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
solution = _load("lab03_solution", LAB_ROOT / "solution" / "main.py")


def _fake_response(text: str):
    """Build the minimal response shape that text_of understands."""
    return SimpleNamespace(content=[SimpleNamespace(type="text", text=text)])


def test_classify_returns_a_known_route(monkeypatch):
    """A well-behaved model label lands inside the closed set."""
    monkeypatch.setattr(
        solution, "complete", lambda messages, **kwargs: _fake_response(" Refund \n")
    )
    label = solution.classify("I want my money back for the blender.")
    assert label in solution.ROUTES
    assert label == "refund"


def test_an_unrecognised_label_falls_back_to_other(monkeypatch):
    """A label outside ROUTES is untrusted output and must not propagate."""
    monkeypatch.setattr(
        solution, "complete", lambda messages, **kwargs: _fake_response("billing")
    )
    assert solution.classify("A question about invoices.") == "other"


def test_handle_uses_the_prompt_for_the_named_route(monkeypatch):
    """An unknown route name lands on the 'other' prompt rather than raising."""
    seen: dict[str, str | None] = {}

    def fake_complete(messages, *, system=None, **kwargs):
        seen["system"] = system
        return _fake_response("an answer")

    monkeypatch.setattr(solution, "complete", fake_complete)
    answer = solution.handle("no-such-route", "Where is my order?")
    assert seen["system"] == solution.ROUTES["other"]
    assert answer == "an answer"


def test_route_and_answer_reports_the_route_taken(monkeypatch):
    """The result carries both route and answer, so the decision is loggable."""
    monkeypatch.setattr(solution, "classify", lambda question: "refund")
    monkeypatch.setattr(solution, "handle", lambda route, question: "the answer")
    result = solution.route_and_answer("I want my money back.")
    assert result == {"route": "refund", "answer": "the answer"}


def test_misroute_rate_matches_a_hand_counted_example(monkeypatch):
    """Two known disagreements out of ten give 0.2; an empty set gives 0.0."""
    labelled = [(f"question {index}", "refund") for index in range(10)]
    # The stub misroutes exactly the first two questions.
    wrong = {"question 0", "question 1"}
    monkeypatch.setattr(
        solution,
        "classify",
        lambda question: "other" if question in wrong else "refund",
    )
    assert solution.misroute_rate(labelled) == 0.2
    assert solution.misroute_rate([]) == 0.0
