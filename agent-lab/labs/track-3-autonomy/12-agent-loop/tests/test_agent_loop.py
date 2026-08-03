"""Tests for Lab 12 - The agent loop.

Budgets, retries, and the non-progress detector are pure logic. Every test
drives the loop with a scripted stand-in for the model and the tools, so
the whole file runs offline without an API key.
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
solution = _load("lab12_solution", LAB_ROOT / "solution" / "main.py")


def _usage() -> SimpleNamespace:
    """Fixed token counts so scripted steps have a predictable cost."""
    return SimpleNamespace(
        input_tokens=200,
        output_tokens=40,
        cache_read_input_tokens=0,
        cache_creation_input_tokens=0,
    )


def _tool_model(vary_arguments: bool):
    """A stub model that always asks for one more tool call.

    Varying the arguments makes the run look busy so only a budget can stop
    it; repeating them makes the non-progress detector fire first.
    """
    counter = iter(range(1_000_000))

    def call(messages):
        n = next(counter)
        order = f"A-{n}" if vary_arguments else "A-100"
        block = SimpleNamespace(
            type="tool_use",
            id=f"toolu_{n}",
            name="lookup_order",
            input={"order_id": order},
        )
        return SimpleNamespace(
            content=[block], stop_reason="tool_use", usage=_usage()
        )

    return call


def test_the_loop_stops_at_the_step_budget():
    """A model that never finishes is stopped by max_steps, by name."""
    budget = solution.AgentBudget(max_steps=3, max_usd=100.0, max_seconds=60.0)
    result = solution.agent_loop(
        "Check every order.", budget=budget, model_call=_tool_model(True)
    )
    assert result["stop_reason"] == "max_steps"
    assert result["steps"] == 3


def test_the_cost_ceiling_stops_a_run_before_the_step_budget(monkeypatch):
    """High per-step spend trips max_usd while steps remain."""
    # The cost ceiling prices steps against the default model; an unpriced
    # LAB_MODEL override would silently disable it and break the test.
    monkeypatch.delenv("LAB_MODEL", raising=False)
    budget = solution.AgentBudget(max_steps=100, max_usd=0.001, max_seconds=60.0)
    result = solution.agent_loop(
        "Check every order.", budget=budget, model_call=_tool_model(True)
    )
    assert result["stop_reason"] == "max_usd"
    assert result["steps"] < budget.max_steps


def test_run_tool_with_retry_retries_then_surrenders():
    """A tool that always fails is tried exactly `attempts` times, then the
    error comes back as a result instead of an exception."""
    calls = {"n": 0}

    def always_fails(arguments):
        calls["n"] += 1
        raise TimeoutError("network down")

    output, is_error = solution.run_tool_with_retry(
        "lookup_order", {}, attempts=3, executor=always_fails
    )
    assert calls["n"] == 3
    assert is_error is True
    assert "3 attempts" in output


def test_run_tool_with_retry_returns_a_recovered_result():
    """A transient failure followed by a success is not an error."""
    calls = {"n": 0}

    def flaky(arguments):
        calls["n"] += 1
        if calls["n"] == 1:
            raise TimeoutError("transient network failure")
        return "recovered on the second attempt"

    output, is_error = solution.run_tool_with_retry(
        "lookup_order", {}, executor=flaky
    )
    assert is_error is False
    assert output == "recovered on the second attempt"


def test_detect_no_progress_flags_a_repeated_action():
    """Three identical action and observation pairs are a stuck run."""
    pair = ("lookup_order([('order_id', 'A-100')])", "Order A-100: shipped.")
    assert solution.detect_no_progress([pair, pair, pair]) is True


def test_detect_no_progress_ignores_genuine_variety():
    """Different actions are a working run, not a stuck one."""
    history = [
        ("lookup_order([('order_id', 'A-100')])", "Order A-100: shipped."),
        ("lookup_order([('order_id', 'A-200')])", "Order A-200: payment failed."),
        ("lookup_order([('order_id', 'A-300')])", "Error: unknown order."),
    ]
    assert solution.detect_no_progress(history) is False


def test_every_exit_path_sets_a_stop_reason():
    """Success and stagnation both name their stop reason, so a caller
    never has to infer why a run ended."""

    def answers(messages):
        block = SimpleNamespace(type="text", text="Order A-100 shipped on Monday.")
        return SimpleNamespace(
            content=[block], stop_reason="end_turn", usage=_usage()
        )

    budget = solution.AgentBudget(max_steps=10, max_usd=100.0, max_seconds=60.0)
    done = solution.agent_loop("Check A-100.", budget=budget, model_call=answers)
    assert done["stop_reason"] == "completed"
    assert done["answer"] == "Order A-100 shipped on Monday."

    stuck = solution.agent_loop(
        "Check A-100.", budget=budget, model_call=_tool_model(False)
    )
    assert stuck["stop_reason"] == "no_progress"
