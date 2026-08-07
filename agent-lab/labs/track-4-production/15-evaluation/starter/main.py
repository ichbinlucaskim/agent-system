"""Lab 15 - Evaluation (starter).

Goal: Build a regression suite for an LLM system: deterministic assertions
where they apply, rubric-based LLM-as-judge scoring where they do not, and
a pass rate report across repeated runs rather than a single-run verdict.

Fill in each function below. Every one carries a TODO describing what to
do and which step of the README it maps to. Run the tests with:

    pytest labs/track-4-production/15-evaluation/tests -v
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable


@dataclass(frozen=True)
class Check:
    """One deterministic check."""

    # TODO: step 1. fn returns None on pass and a human-readable reason on
    # failure, so a failing check is a bug report rather than a bare boolean.
    name: str = ""
    fn: Callable[[str], str | None] | None = None


@dataclass(frozen=True)
class Case:
    """One evaluation case: an id, an input, and its deterministic checks."""

    # TODO: step 1. id, input, and checks. Keeping cases as data means adding
    # a case is adding a row, not writing a test function.
    id: str = ""
    input: str = ""
    checks: list[Check] = field(default_factory=list)


def run_deterministic(case: Any, output: str) -> dict[str, Any]:
    """Apply every deterministic check and report per-check results."""
    # TODO: step 2. Return per-check {name, passed, reason}. The reason on
    # failure is the bug report.
    raise NotImplementedError


def parse_judgement(reply: str) -> dict[str, Any]:
    """Parse a judge reply into {'score', 'reason'} or {'error', 'raw'}."""
    # TODO: step 3. A reply that does not parse is an error, never a score of
    # zero — folding parse failures into the metric lets judge bugs look like
    # regressions in the system under test.
    raise NotImplementedError


def judge(case: Any, output: str, rubric: str) -> dict[str, Any]:
    """Score an output against a rubric using a model call."""
    # TODO: step 3. Ask for structured JSON and pass the reply to parse_judgement.
    raise NotImplementedError


def run_suite(
    cases: list[Any],
    *,
    runs: int = 3,
    rubric: str | None = None,
    target: Callable[[str], str] | None = None,
    judge_fn: Callable[[Any, str, str], dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Run every case several times and collect the results."""
    # TODO: step 4. Keep raw outputs. Pass rate is deterministic only; when
    # rubric is set, store judgement alongside but do not fold it into the rate.
    # target / judge_fn are injection points for offline tests.
    raise NotImplementedError


def format_report(results: dict[str, Any]) -> str:
    """Render pass rates, flaky cases, and failures as text."""
    # TODO: step 5. Label rates strictly between 0 and 1 as flaky. List every
    # failing check with its output. List judge errors separately.
    raise NotImplementedError


def main() -> int:
    """Run the lab end to end and print what happened."""
    # TODO: step 6. Run the suite twice against a scripted target — change
    # one behaviour between the runs — and print both reports so the
    # before/after comparison is visible.
    raise NotImplementedError


if __name__ == "__main__":
    raise SystemExit(main())
