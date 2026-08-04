"""Tests for Lab 04 - Parallelization.

Ordering, failure isolation, voting, and merging are deterministic once the
per-section model call is stubbed, so every test runs offline and no API key
is needed.
"""

from __future__ import annotations

import importlib.util
import itertools
import sys
import threading
import time
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
solution = _load("lab04_solution", LAB_ROOT / "solution" / "main.py")

SECTIONS = [
    {"name": "correctness", "instruction": "check facts"},
    {"name": "tone", "instruction": "check tone"},
    {"name": "legal-risk", "instruction": "check risk"},
]


def test_run_sections_preserves_input_order(monkeypatch):
    """A later section finishing first must not reorder the results."""
    delays = {"correctness": 0.05, "tone": 0.0, "legal-risk": 0.0}

    def fake_run(section_spec, text):
        # The first section sleeps, so the others complete before it.
        time.sleep(delays[section_spec["name"]])
        return f"result for {section_spec['name']}"

    monkeypatch.setattr(solution, "_run_one_section", fake_run)
    results = solution.run_sections(SECTIONS, "the text")
    assert [entry["name"] for entry in results] == [
        "correctness",
        "tone",
        "legal-risk",
    ]
    assert results[1]["result"] == "result for tone"


def test_a_failed_section_does_not_lose_the_others(monkeypatch):
    """One raising call yields an error entry while the rest still return."""

    def fake_run(section_spec, text):
        if section_spec["name"] == "tone":
            raise RuntimeError("boom")
        return f"result for {section_spec['name']}"

    monkeypatch.setattr(solution, "_run_one_section", fake_run)
    results = solution.run_sections(SECTIONS, "the text")
    assert len(results) == len(SECTIONS)
    by_name = {entry["name"]: entry for entry in results}
    assert by_name["tone"]["result"] is None
    assert "boom" in by_name["tone"]["error"]
    assert by_name["correctness"]["error"] is None
    assert by_name["legal-risk"]["result"] == "result for legal-risk"


def test_vote_keeps_the_answers_it_got_when_one_call_fails(monkeypatch):
    """A lost call costs one vote, not the whole batch."""
    seen = itertools.count(1)
    guard = threading.Lock()

    def flaky(question):
        with guard:
            index = next(seen)
        if index == 2:
            raise RuntimeError("rate limited")
        return "Yes."

    monkeypatch.setattr(solution, "_ask_once", flaky)
    answers, errors = solution.vote("is it safe?", n=3)
    assert answers == ["yes", "yes"]
    assert len(errors) == 1
    assert "rate limited" in errors[0]
    # Agreement is measured over the votes that arrived, not over n.
    assert solution.majority(answers) == ("yes", 1.0)


def test_a_vote_that_loses_every_call_reports_no_agreement(monkeypatch):
    """Losing every call yields an empty vote rather than an exception."""

    def always_fails(question):
        raise RuntimeError("boom")

    monkeypatch.setattr(solution, "_ask_once", always_fails)
    answers, errors = solution.vote("is it safe?", n=3)
    assert answers == []
    assert len(errors) == 3
    assert solution.majority(answers) == ("", 0.0)


def test_majority_picks_the_modal_answer_and_reports_agreement():
    """Two of three votes for 'yes' return ('yes', 2/3)."""
    answer, agreement = solution.majority(["yes", "yes", "no"])
    assert answer == "yes"
    assert agreement == 2 / 3


def test_majority_breaks_ties_deterministically():
    """A tie resolves the same way on every call, by first appearance."""
    outcomes = {solution.majority(["a", "b"]) for _ in range(10)}
    assert outcomes == {("a", 0.5)}


def test_majority_handles_an_empty_vote_list():
    """No votes returns ('', 0.0) rather than raising."""
    assert solution.majority([]) == ("", 0.0)


def test_merge_sections_keeps_every_section_labelled():
    """Each section name appears in the merged report."""
    results = [
        {"name": "correctness", "result": "two errors found", "error": None},
        {"name": "tone", "result": None, "error": "RuntimeError: boom"},
    ]
    report = solution.merge_sections(results)
    assert "correctness" in report
    assert "tone" in report
    assert "two errors found" in report
    assert "boom" in report
