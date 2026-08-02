"""Step-level tracing for agent runs.

A trace turns an opaque run into a list of records you can count, price, and
read. Every lab that makes more than one model call should wrap each call in a
step so that lab 16 has something to report on.

Usage:

    trace = Trace()
    with trace.step("classify", question=question) as step:
        response = complete(messages)
        step.record_usage(response)
        step.output = text_of(response)

    print(trace.render_text_report())
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any


@dataclass
class StepRecord:
    """One recorded step of a run."""

    name: str
    inputs: dict[str, Any] = field(default_factory=dict)
    output: Any = None
    duration_s: float = 0.0
    input_tokens: int = 0
    output_tokens: int = 0
    cache_read_tokens: int = 0
    cache_creation_tokens: int = 0
    error: str | None = None

    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens

    def record_usage(self, response: Any) -> None:
        """Copy token counts off a Messages API response."""
        usage = getattr(response, "usage", None)
        if usage is None:
            return
        self.input_tokens += getattr(usage, "input_tokens", 0) or 0
        self.output_tokens += getattr(usage, "output_tokens", 0) or 0
        self.cache_read_tokens += getattr(usage, "cache_read_input_tokens", 0) or 0
        self.cache_creation_tokens += (
            getattr(usage, "cache_creation_input_tokens", 0) or 0
        )


class _StepContext:
    """Context manager that times one step and appends it to a trace."""

    def __init__(self, trace: "Trace", record: StepRecord) -> None:
        self._trace = trace
        self._record = record
        self._started = 0.0

    def __enter__(self) -> StepRecord:
        self._started = time.perf_counter()
        return self._record

    def __exit__(self, exc_type, exc, tb) -> bool:
        self._record.duration_s = time.perf_counter() - self._started
        if exc is not None:
            self._record.error = f"{exc_type.__name__}: {exc}"
        self._trace.records.append(self._record)
        return False


class Trace:
    """Collects StepRecord entries for one run."""

    def __init__(self, name: str = "run") -> None:
        self.name = name
        self.records: list[StepRecord] = []

    def step(self, name: str, **inputs: Any) -> _StepContext:
        """Open a step. The context manager yields the StepRecord."""
        return _StepContext(self, StepRecord(name=name, inputs=dict(inputs)))

    @property
    def total_duration_s(self) -> float:
        return sum(record.duration_s for record in self.records)

    @property
    def total_input_tokens(self) -> int:
        return sum(record.input_tokens for record in self.records)

    @property
    def total_output_tokens(self) -> int:
        return sum(record.output_tokens for record in self.records)

    def render_text_report(self) -> str:
        """Render this trace as a plain text table."""
        return render_text_report(self.records, title=self.name)


def _truncate(value: Any, limit: int = 48) -> str:
    text = " ".join(str(value).split())
    if len(text) <= limit:
        return text
    return text[: limit - 3] + "..."


def render_text_report(records: list[StepRecord], title: str = "run") -> str:
    """Render a list of step records as a plain text table.

    Kept as a module level function so that labs can render records collected
    by something other than a Trace instance.
    """
    header = f"{'step':<24}{'secs':>8}{'in':>10}{'out':>10}  output"
    lines = [f"trace: {title}", header, "-" * len(header)]
    for record in records:
        marker = " [error]" if record.error else ""
        lines.append(
            f"{_truncate(record.name, 24):<24}"
            f"{record.duration_s:>8.2f}"
            f"{record.input_tokens:>10}"
            f"{record.output_tokens:>10}"
            f"  {_truncate(record.error or record.output)}{marker}"
        )
    lines.append("-" * len(header))
    total_in = sum(record.input_tokens for record in records)
    total_out = sum(record.output_tokens for record in records)
    total_s = sum(record.duration_s for record in records)
    lines.append(
        f"{'total (' + str(len(records)) + ' steps)':<24}"
        f"{total_s:>8.2f}{total_in:>10}{total_out:>10}"
    )
    return "\n".join(lines)
