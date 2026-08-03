"""Lab 16 - Observability (reference solution).

A run total cannot say why a run cost what it cost; a per-step trace can.
One structured record per step, cost and latency attributed to the step
level, and a plain text report that shows where the budget went.
"""

from __future__ import annotations

import math
import time
from types import SimpleNamespace
from typing import Any, Callable

from common.cost import TokenUsage, estimate_cost
from common.tracing import StepRecord, Trace


def trace_step(trace: Trace, name: str, fn: Callable[[], Any], **inputs: Any) -> Any:
    """Run a callable and record one step for it.

    All bookkeeping lives here so call sites stay one line. The step context
    manager appends the record on exit even when fn raises, so a failing step
    is recorded with its error and its duration before the exception
    propagates; a trace holding only successes would under-report a system
    that is retrying.
    """
    with trace.step(name, **inputs) as step:
        result = fn()
        # record_usage is a no-op for results without a usage attribute, so
        # non-API steps can go through the same wrapper.
        step.record_usage(result)
        step.output = result
        return result


def _usage_of_record(record: StepRecord) -> TokenUsage:
    """Rebuild a TokenUsage from the counts a step recorded."""
    return TokenUsage(
        input_tokens=record.input_tokens,
        output_tokens=record.output_tokens,
        cache_read_tokens=record.cache_read_tokens,
        cache_creation_tokens=record.cache_creation_tokens,
    )


def _cost_of_record(record: StepRecord, model: str) -> float:
    return estimate_cost(model, _usage_of_record(record))


def attribute_cost(trace: Trace, model: str) -> dict[str, float]:
    """Convert per-step usage into per-step dollars.

    Steps sharing a name are summed into one entry. The parts are checked
    against the whole: pricing is linear in tokens, so any mismatch means a
    step's usage is being missed, not a rounding artifact.
    """
    costs: dict[str, float] = {}
    total_usage = TokenUsage()
    for record in trace.records:
        costs[record.name] = costs.get(record.name, 0.0) + _cost_of_record(
            record, model
        )
        total_usage = total_usage + _usage_of_record(record)

    whole = estimate_cost(model, total_usage)
    if not math.isclose(sum(costs.values()), whole, rel_tol=1e-9, abs_tol=1e-12):
        raise AssertionError(
            f"per-step costs sum to {sum(costs.values()):.10f} but the run "
            f"total is {whole:.10f}; a step is being missed"
        )
    return costs


def slowest_steps(trace: Trace, n: int = 3) -> list[StepRecord]:
    """The n steps that took the longest."""
    return sorted(trace.records, key=lambda r: r.duration_s, reverse=True)[:n]


def costliest_steps(trace: Trace, model: str, n: int = 3) -> list[StepRecord]:
    """The n steps that spent the most.

    Usually a different list from slowest_steps: a step can be slow because
    it waits and cheap because it sends little, and optimising the wrong one
    wastes the week.
    """
    return sorted(
        trace.records, key=lambda r: _cost_of_record(r, model), reverse=True
    )[:n]


def render_report(trace: Trace, model: str) -> str:
    """Render the full text report for a run.

    Plain text on purpose: it works in a terminal, in CI output, and in a
    pull request comment, with no service to run.
    """
    header = f"{'step':<20}{'secs':>8}{'in':>10}{'out':>10}{'cost $':>12}  note"
    lines = [f"trace: {trace.name} (model {model})", header, "-" * len(header)]

    total_usage = TokenUsage()
    for record in trace.records:
        note = f"error: {record.error}" if record.error else ""
        lines.append(
            f"{record.name:<20}"
            f"{record.duration_s:>8.2f}"
            f"{record.input_tokens:>10}"
            f"{record.output_tokens:>10}"
            f"{_cost_of_record(record, model):>12.6f}"
            f"  {note}"
        )
        total_usage = total_usage + _usage_of_record(record)

    lines.append("-" * len(header))
    lines.append(
        f"{'total (' + str(len(trace.records)) + ' steps)':<20}"
        f"{trace.total_duration_s:>8.2f}"
        f"{total_usage.input_tokens:>10}"
        f"{total_usage.output_tokens:>10}"
        f"{estimate_cost(model, total_usage):>12.6f}"
    )

    lines.append("")
    lines.append("slowest steps:")
    for record in slowest_steps(trace):
        lines.append(f"  {record.name:<20}{record.duration_s:>8.2f}s")
    lines.append("costliest steps:")
    for record in costliest_steps(trace, model):
        lines.append(f"  {record.name:<20}${_cost_of_record(record, model):.6f}")
    return "\n".join(lines)


def _fake_response(
    input_tokens: int, output_tokens: int, wait_s: float = 0.0
) -> Any:
    """A response-shaped object carrying only usage, for the offline demo.

    wait_s simulates latency so duration and cost can disagree, which they
    do in real runs.
    """
    if wait_s:
        time.sleep(wait_s)
    return SimpleNamespace(
        usage=SimpleNamespace(
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cache_read_input_tokens=0,
            cache_creation_input_tokens=0,
        )
    )


def main() -> int:
    """Trace a simulated orchestrator run and print the report.

    The steps are simulated so the bookkeeping is visible without an API
    key. To trace a real run, wrap each call of the lab 05 orchestrator in
    trace_step; the records and the report do not change shape.
    """
    model = "claude-opus-5"
    trace = Trace("orchestrator-demo")

    # worker-search is slow but cheap, synthesize is fast but expensive, so
    # the two top-n lists disagree, which is the point of having both.
    trace_step(trace, "plan", lambda: _fake_response(400, 150, wait_s=0.01))
    trace_step(trace, "worker-search", lambda: _fake_response(900, 300, wait_s=0.12))
    trace_step(
        trace, "worker-summarize", lambda: _fake_response(1_200, 400, wait_s=0.05)
    )
    trace_step(trace, "synthesize", lambda: _fake_response(9_000, 800, wait_s=0.02))

    def flaky() -> Any:
        raise TimeoutError("upstream took too long")

    # A failing step still consumed time and must appear in the trace.
    try:
        trace_step(trace, "worker-flaky", flaky)
    except TimeoutError:
        pass

    print(render_report(trace, model))

    costs = attribute_cost(trace, model)
    dominant = max(costs, key=costs.get)
    share = costs[dominant] / sum(costs.values())
    print(f"\n{dominant} carries {share:.0%} of the bill")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
