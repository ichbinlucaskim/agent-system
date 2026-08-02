"""Lab 16 - Observability (starter).

Goal: Record a structured trace for every step of a run, attribute cost and latency to individual steps rather than whole runs, and render a text report that shows where a run spent its budget.

Fill in each function below. Every one carries a TODO describing what to
do and which step of the README it maps to. Run the tests with:

    pytest labs/track-4-production/16-observability/tests -v
"""

from __future__ import annotations

from typing import Any, Callable

from common.cost import TokenUsage
from common.tracing import StepRecord, Trace


def trace_step(trace: Trace, name: str, fn: Callable[[], Any], **inputs: Any) -> Any:
    """Run a callable and record one step for it."""
    # TODO: step 2. Record duration, usage, and error without the caller writing bookkeeping at each call site. A step that raises must still be recorded before the exception propagates.
    raise NotImplementedError


def attribute_cost(trace: Trace, model: str) -> dict[str, float]:
    """Convert per-step usage into per-step dollars."""
    # TODO: step 3. Use common.cost.estimate_cost per step. Assert to yourself that the parts sum to the whole; a mismatch means a step is being missed.
    raise NotImplementedError


def slowest_steps(trace: Trace, n: int = 3) -> list[StepRecord]:
    """The n steps that took the longest."""
    # TODO: step 4. Sort by duration descending. This is usually not the same list as costliest_steps, which is the point of having both.
    raise NotImplementedError


def costliest_steps(trace: Trace, model: str, n: int = 3) -> list[StepRecord]:
    """The n steps that spent the most."""
    # TODO: step 4. Sort by attributed cost descending. Optimising the slowest step when the costliest is a different one wastes the week.
    raise NotImplementedError


def render_report(trace: Trace, model: str) -> str:
    """Render the full text report for a run."""
    # TODO: step 5. One line per step with duration, tokens, and cost, then totals, then the two top-n lists. Plain text so it works in a terminal and in CI.
    raise NotImplementedError


def main() -> int:
    """Run the lab end to end and print what happened."""
    # TODO: final step. Wire the functions above together and print
    # enough that the behaviour described in the README is visible.
    raise NotImplementedError


if __name__ == "__main__":
    raise SystemExit(main())
