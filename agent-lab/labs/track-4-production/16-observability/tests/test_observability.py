"""Tests for Lab 16 - Observability.

Traces are built from response-shaped stubs that carry only usage counts, so
every test runs offline. No test needs an API key.
"""

from __future__ import annotations

import importlib.util
import math
import sys
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest


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
solution = _load("lab16_solution", LAB_ROOT / "solution" / "main.py")

MODEL = "claude-opus-5"


def _fake_response(input_tokens: int, output_tokens: int) -> Any:
    """A response-shaped object carrying only usage, like the demo uses."""
    return SimpleNamespace(
        usage=SimpleNamespace(
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cache_read_input_tokens=0,
            cache_creation_input_tokens=0,
        )
    )


def test_each_step_is_recorded_exactly_once():
    """A run of three steps produces three records, in call order."""
    trace = solution.Trace("test-run")
    for name in ("plan", "search", "synthesize"):
        solution.trace_step(trace, name, lambda: _fake_response(100, 10))
    assert [record.name for record in trace.records] == [
        "plan",
        "search",
        "synthesize",
    ]


def test_a_failing_step_is_still_recorded():
    """A step that raises appears in the trace with its error and duration."""
    trace = solution.Trace("test-run")

    def flaky() -> Any:
        raise TimeoutError("upstream took too long")

    with pytest.raises(TimeoutError):
        solution.trace_step(trace, "worker-flaky", flaky)
    assert len(trace.records) == 1
    record = trace.records[0]
    assert record.error is not None
    assert "upstream took too long" in record.error
    assert record.duration_s > 0.0


def test_per_step_costs_sum_to_the_run_total():
    """Attributed per-step costs equal the cost of the summed usage."""
    trace = solution.Trace("test-run")
    solution.trace_step(trace, "cheap", lambda: _fake_response(100, 10))
    solution.trace_step(trace, "pricey", lambda: _fake_response(50_000, 4_000))
    costs = solution.attribute_cost(trace, MODEL)
    total_usage = solution.TokenUsage(
        input_tokens=trace.total_input_tokens,
        output_tokens=trace.total_output_tokens,
    )
    whole = solution.estimate_cost(MODEL, total_usage)
    assert math.isclose(sum(costs.values()), whole, rel_tol=1e-9)


def test_slowest_and_costliest_can_be_different_steps():
    """A slow but cheap step and a fast but pricey step rank differently."""
    trace = solution.Trace("test-run")
    trace.records.append(
        solution.StepRecord(
            name="slow-cheap", duration_s=2.0, input_tokens=100, output_tokens=10
        )
    )
    trace.records.append(
        solution.StepRecord(
            name="fast-pricey",
            duration_s=0.01,
            input_tokens=90_000,
            output_tokens=9_000,
        )
    )
    assert solution.slowest_steps(trace, n=1)[0].name == "slow-cheap"
    assert solution.costliest_steps(trace, MODEL, n=1)[0].name == "fast-pricey"


def test_the_report_names_every_step():
    """Every step name appears in the report, so nothing is silently missing."""
    trace = solution.Trace("test-run")
    names = ("plan", "worker-search", "synthesize")
    for name in names:
        solution.trace_step(trace, name, lambda: _fake_response(200, 20))
    report = solution.render_report(trace, MODEL)
    for name in names:
        assert name in report
