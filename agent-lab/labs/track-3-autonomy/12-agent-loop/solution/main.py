"""Lab 12 - The agent loop (reference solution).

A workflow becomes an agent when the model decides what happens next. The
loop itself is a few lines; nearly everything here is about stopping: a
step budget, a cost ceiling, a wall-clock deadline, retries that end by
handing the error to the model, and a detector for a run that repeats
itself instead of progressing.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from types import SimpleNamespace
from typing import Any, Callable

from common.client import complete_with_tools, resolve_model, text_of, tool_uses
from common.cost import UnknownModelError, estimate_cost, usage_of
from common.tracing import Trace

SYSTEM = (
    "You are an order-support agent. Use lookup_order to read order status. "
    "When you have the answer, state it plainly and stop calling tools."
)

ORDERS: dict[str, str] = {
    "A-100": "shipped on Monday, arriving Thursday",
    "A-200": "payment failed, awaiting a new card",
}

TOOLS: list[dict[str, Any]] = [
    {
        "name": "lookup_order",
        "description": "Look up the current status of one order by its id.",
        "input_schema": {
            "type": "object",
            "properties": {
                "order_id": {
                    "type": "string",
                    "description": "The order identifier, for example A-100.",
                }
            },
            "required": ["order_id"],
        },
    }
]


def _lookup_order(arguments: dict[str, Any]) -> str:
    order_id = str(arguments.get("order_id", "")).strip().upper()
    if order_id not in ORDERS:
        known = ", ".join(sorted(ORDERS))
        raise KeyError(f"unknown order {order_id!r}, known orders are {known}")
    return f"Order {order_id}: {ORDERS[order_id]}."


TOOL_RUNNERS: dict[str, Callable[[dict[str, Any]], str]] = {
    "lookup_order": _lookup_order,
}


@dataclass(frozen=True)
class AgentBudget:
    """Independent ceilings on steps, spend, and wall-clock time."""

    # The three ceilings fail differently: one step can be far more expensive
    # than another, and a slow tool can burn the deadline while spending
    # nothing, so they are never collapsed into one number.
    max_steps: int = 10
    max_usd: float = 1.0
    max_seconds: float = 120.0


@dataclass
class RunState:
    """What one run has consumed so far."""

    steps: int = 0
    usd: float = 0.0
    started: float = field(default_factory=time.perf_counter)

    @property
    def elapsed_s(self) -> float:
        return time.perf_counter() - self.started


def is_exhausted(budget: Any, state: Any) -> tuple[bool, str]:
    """Report whether any budget is spent, and which one."""
    # The caller needs the reason, not just the fact: "max_usd" and
    # "max_steps" call for different fixes.
    if state.steps >= budget.max_steps:
        return (True, "max_steps")
    if state.usd >= budget.max_usd:
        return (True, "max_usd")
    if state.elapsed_s >= budget.max_seconds:
        return (True, "max_seconds")
    return (False, "")


def run_tool_with_retry(
    name: str,
    arguments: dict[str, Any],
    *,
    attempts: int = 2,
    executor: Callable[[dict[str, Any]], str] | None = None,
) -> tuple[str, bool]:
    """Retry a failing tool, then hand the error to the model."""
    runner = executor if executor is not None else TOOL_RUNNERS.get(name)
    if runner is None:
        return (f"Error: unknown tool {name!r}.", True)
    last_error = ""
    for _ in range(attempts):
        try:
            return (str(runner(arguments)), False)
        except Exception as exc:
            last_error = f"{type(exc).__name__}: {exc}"
    # A retry was our decision; past the last attempt the error becomes a
    # tool result, and choosing a different approach becomes the model's.
    return (
        f"Error: tool {name!r} failed after {attempts} attempts. {last_error}",
        True,
    )


def detect_no_progress(history: list[tuple[str, str]], *, window: int = 3) -> bool:
    """Detect a run repeating the same action and observation."""
    if len(history) < window:
        return False
    # A stuck agent does not crash, it repeats: same call, same result, same
    # confidence. Identical hashes across the window are that signature.
    digests = {hash(pair) for pair in history[-window:]}
    return len(digests) == 1


def _cost_of(response: Any) -> float:
    try:
        return estimate_cost(resolve_model(None), usage_of(response))
    except UnknownModelError:
        # An unpriced model would silently disable the cost ceiling; treat
        # its spend as zero but keep the other budgets in force.
        return 0.0


def agent_loop(
    task: str,
    *,
    budget: Any,
    tools: list[dict[str, Any]] | None = None,
    model_call: Callable[[list[dict[str, Any]]], Any] | None = None,
    executor: Callable[[dict[str, Any]], str] | None = None,
) -> dict[str, Any]:
    """Run the autonomous loop until done or stopped.

    model_call and executor exist so tests can drive the loop with a stub;
    by default it talks to the real model and the real tools.
    """
    tools = TOOLS if tools is None else tools
    call = model_call or (
        lambda messages: complete_with_tools(messages, tools, system=SYSTEM)
    )
    trace = Trace("agent-loop")
    state = RunState()
    messages: list[dict[str, Any]] = [{"role": "user", "content": task}]
    history: list[tuple[str, str]] = []
    answer = ""
    stop_reason = ""

    while True:
        # Budgets are checked before each step so the step that would exceed
        # them is never taken.
        spent, which = is_exhausted(budget, state)
        if spent:
            stop_reason = which
            break

        with trace.step(f"step-{state.steps + 1}") as step:
            response = call(messages)
            step.record_usage(response)
            step.output = text_of(response)
        state.steps += 1
        state.usd += _cost_of(response)
        messages.append({"role": "assistant", "content": response.content})

        if response.stop_reason != "tool_use":
            answer = text_of(response)
            stop_reason = "completed"
            break

        results: list[dict[str, Any]] = []
        for block in tool_uses(response):
            arguments = dict(block.input)
            output, is_error = run_tool_with_retry(
                block.name, arguments, executor=executor
            )
            action = f"{block.name}({sorted(arguments.items())!r})"
            history.append((action, output))
            results.append(
                {
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": output,
                    "is_error": is_error,
                }
            )
        messages.append({"role": "user", "content": results})

        if detect_no_progress(history):
            stop_reason = "no_progress"
            break

    # Every exit path above set a stop_reason; a caller must never have to
    # infer why a run ended.
    return {
        "answer": answer,
        "stop_reason": stop_reason,
        "steps": state.steps,
        "usd": round(state.usd, 6),
        "trace": trace,
    }


def _scripted_model(vary_arguments: bool) -> Callable[[list[dict[str, Any]]], Any]:
    """A stub model that always asks for one more tool call.

    With vary_arguments the run looks busy and only a budget stops it;
    without it the run repeats itself and the non-progress detector fires
    before the step budget does.
    """
    counter = iter(range(1_000_000))

    def call(messages: list[dict[str, Any]]) -> Any:
        n = next(counter)
        order = f"A-{n}" if vary_arguments else "A-100"
        block = SimpleNamespace(
            type="tool_use",
            id=f"toolu_{n}",
            name="lookup_order",
            input={"order_id": order},
        )
        usage = SimpleNamespace(
            input_tokens=200,
            output_tokens=40,
            cache_read_input_tokens=0,
            cache_creation_input_tokens=0,
        )
        return SimpleNamespace(content=[block], stop_reason="tool_use", usage=usage)

    return call


def main() -> int:
    """Run scripted loops offline and print which condition stopped each."""
    budget = AgentBudget(max_steps=4, max_usd=1.0, max_seconds=30.0)

    busy = agent_loop(
        "Check every order.", budget=budget, model_call=_scripted_model(True)
    )
    print(f"busy run stopped by {busy['stop_reason']} after {busy['steps']} steps")
    print(busy["trace"].render_text_report())
    print()

    stuck = agent_loop(
        "Check order A-100.", budget=budget, model_call=_scripted_model(False)
    )
    print(f"stuck run stopped by {stuck['stop_reason']} after {stuck['steps']} steps")
    print()

    calls = {"n": 0}

    def flaky(arguments: dict[str, Any]) -> str:
        calls["n"] += 1
        if calls["n"] == 1:
            raise TimeoutError("transient network failure")
        return "recovered on the second attempt"

    output, is_error = run_tool_with_retry("lookup_order", {}, executor=flaky)
    print(f"retry demo: error={is_error} output={output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
