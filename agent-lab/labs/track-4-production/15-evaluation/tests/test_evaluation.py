"""Tests for Lab 15 - Evaluation.

The suite machinery accepts an injected target and judge, so every test runs
offline against scripted outputs. No test needs an API key.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from typing import Callable


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
solution = _load("lab15_solution", LAB_ROOT / "solution" / "main.py")


def _contains(needle: str) -> Callable[[str], str | None]:
    def check(output: str) -> str | None:
        if needle in output:
            return None
        return f"expected the output to mention {needle!r}"

    return check


def test_a_deterministic_check_reports_its_failure_reason():
    """A failing check returns a reason string, not just False."""
    case = solution.Case(
        "returns",
        "How long do I have to return an item?",
        [solution.Check("mentions 30 days", _contains("30 days"))],
    )
    result = solution.run_deterministic(case, "Returns are accepted eventually.")
    assert result["passed"] is False
    check = result["checks"][0]
    assert check["passed"] is False
    assert isinstance(check["reason"], str)
    assert "30 days" in check["reason"]


def test_the_pass_rate_is_computed_across_runs():
    """A case passing 2 of 4 runs reports 0.5, not the last run's verdict."""
    case = solution.Case(
        "cycling", "q", [solution.Check("mentions keyword", _contains("keyword"))]
    )
    outputs = iter(["keyword present", "missing", "keyword present", "missing"])
    results = solution.run_suite(
        [case], runs=4, target=lambda question: next(outputs)
    )
    # The last run fails; a rate of 0.5 proves all four runs were counted.
    assert results["cases"]["cycling"]["pass_rate"] == 0.5


def test_an_intermittent_case_is_marked_flaky():
    """A pass rate strictly between 0 and 1 is labelled flaky in the report."""
    case = solution.Case(
        "sometimes", "q", [solution.Check("mentions keyword", _contains("keyword"))]
    )
    outputs = iter(["keyword present", "missing"])
    results = solution.run_suite(
        [case], runs=2, target=lambda question: next(outputs)
    )
    report = solution.format_report(results)
    assert "flaky" in report


def test_the_report_names_every_failing_case():
    """Each failing case id appears in the failures section of the report."""
    check = solution.Check("mentions keyword", _contains("keyword"))
    cases = [
        solution.Case("alpha", "q1", [check]),
        solution.Case("beta", "q2", [check]),
    ]
    results = solution.run_suite(
        cases, runs=1, target=lambda question: "nothing relevant"
    )
    report = solution.format_report(results)
    assert "failures:" in report
    # The failure lines carry the case id and the run number.
    assert "alpha run 1" in report
    assert "beta run 1" in report


def test_an_unparsable_judge_response_is_recorded_as_an_error():
    """A malformed judge reply is an error entry, never a score of zero."""
    reply = "I would give this a high score, well done."
    result = solution.parse_judgement(reply)
    assert "error" in result
    assert "score" not in result
    # The raw reply is kept so the judge bug can be diagnosed.
    assert result["raw"] == reply
