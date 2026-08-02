"""Lab 15 - Evaluation (starter).

Goal: Build a regression suite for an LLM system: deterministic assertions where they apply, rubric-based LLM-as-judge scoring where they do not, and a pass rate report across repeated runs rather than a single-run verdict.

Fill in each function below. Every one carries a TODO describing what to
do and which step of the README it maps to. Run the tests with:

    pytest labs/track-4-production/15-evaluation/tests -v
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable


class Case:
    """One evaluation case: an id, an input, and its deterministic checks."""

    # TODO: step 1. A dataclass with id, input, and checks. Keeping cases as data means adding a case is adding a row, not writing a test function.


def run_deterministic(case: Any, output: str) -> dict[str, Any]:
    """Apply every deterministic check and report per-check results."""
    # TODO: step 2. Return the reason for each failure, not just a boolean. 'failed' is not a bug report.
    raise NotImplementedError


def judge(case: Any, output: str, rubric: str) -> dict[str, Any]:
    """Score an output against a rubric using a model call."""
    # TODO: step 3. Ask for structured output and parse it. A judge response that does not parse is an error, not a score of zero, or your metric quietly absorbs your bugs.
    raise NotImplementedError


def run_suite(cases: list[Any], *, runs: int = 3, rubric: str | None = None) -> dict[str, Any]:
    """Run every case several times and collect the results."""
    # TODO: step 4. Keep the raw outputs. A report you cannot drill into forces a full re-run to diagnose one failure.
    raise NotImplementedError


def format_report(results: dict[str, Any]) -> str:
    """Render pass rates, flaky cases, and failures as text."""
    # TODO: step 5. A pass rate strictly between 0 and 1 is flaky and should be labelled as such. Name every failing case; an aggregate alone is not actionable.
    raise NotImplementedError


def main() -> int:
    """Run the lab end to end and print what happened."""
    # TODO: final step. Wire the functions above together and print
    # enough that the behaviour described in the README is visible.
    raise NotImplementedError


if __name__ == "__main__":
    raise SystemExit(main())
