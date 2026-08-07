"""Lab 12 - The agent loop (starter).

Goal: Build an autonomous loop that runs until it is done or until a budget
stops it: explicit stop conditions, a step budget, a cost ceiling, a
wall-clock deadline, retries on tool error, and detection of a run that is
no longer making progress.

Fill in each function below. Every one carries a TODO describing what to
do and which step of the README it maps to. Run the tests with:

    pytest labs/track-3-autonomy/12-agent-loop/tests -v
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Callable

from common.tracing import Trace

SYSTEM = (
    "You are an order-support agent. Use lookup_order to read order status. "
    "When you have the answer, state it plainly and stop calling tools."
)

# TODO: step 1. Fill ORDERS with a couple of known order ids and statuses.
ORDERS: dict[str, str] = {}

# TODO: step 1. Define one tool the agent can call (name, description, input_schema).
TOOLS: list[dict[str, Any]] = []

TOOL_RUNNERS: dict[str, Callable[[dict[str, Any]], str]] = {}


@dataclass(frozen=True)
class AgentBudget:
    """Independent ceilings on steps, spend, and wall-clock time."""

    # TODO: step 1. max_steps, max_usd, and max_seconds. They fail differently,
    # so keep them separate rather than collapsing them into one number.
    max_steps: int = 10
    max_usd: float = 1.0
    max_seconds: float = 120.0


@dataclass
class RunState:
    """What one run has consumed so far."""

    # TODO: step 1. Track steps, usd, and a started timestamp so elapsed_s works.
    steps: int = 0
    usd: float = 0.0
    started: float = field(default_factory=time.perf_counter)

    @property
    def elapsed_s(self) -> float:
        # TODO: step 1. Return seconds since started.
        raise NotImplementedError


def is_exhausted(budget: Any, state: Any) -> tuple[bool, str]:
    """Report whether any budget is spent, and which one."""
    # TODO: step 2. Return (True, 'max_steps' | 'max_usd' | 'max_seconds') so
    # the caller learns the reason, not just the fact.
    raise NotImplementedError


def run_tool_with_retry(
    name: str,
    arguments: dict[str, Any],
    *,
    attempts: int = 2,
    executor: Callable[[dict[str, Any]], str] | None = None,
) -> tuple[str, bool]:
    """Retry a failing tool, then hand the error to the model."""
    # TODO: step 3. After the last attempt, return (error_text, True) instead
    # of raising. A retry is your decision; returning the error is the model's.
    # Use executor when provided, otherwise TOOL_RUNNERS[name].
    raise NotImplementedError


def detect_no_progress(history: list[tuple[str, str]], *, window: int = 3) -> bool:
    """Detect a run repeating the same action and observation."""
    # TODO: step 4. Return True when the last `window` (action, observation)
    # pairs are identical. Comparing the pairs themselves — not a hash of the
    # action alone — is what keeps a changing observation counting as progress.
    raise NotImplementedError


def agent_loop(
    task: str,
    *,
    budget: Any,
    tools: list[dict[str, Any]] | None = None,
    model_call: Callable[[list[dict[str, Any]]], Any] | None = None,
    executor: Callable[[dict[str, Any]], str] | None = None,
    state: RunState | None = None,
) -> dict[str, Any]:
    """Run the autonomous loop until done or stopped."""
    # TODO: step 5. Loop until the model stops asking for tools, a budget is
    # exhausted, or non-progress is detected. Check budgets BEFORE each step.
    # Append tool results as a user message so the next model call can see them.
    # Return {'answer', 'stop_reason', 'steps', 'usd', 'trace'}. Every exit
    # path must set a stop_reason, including the successful one.
    #
    # model_call / executor / state are injection points for tests; default
    # them to the real model, TOOL_RUNNERS, and a fresh RunState.
    raise NotImplementedError


def main() -> int:
    """Run the lab end to end and print what happened."""
    # TODO: step 6. Drive three scripted runs that hit max_steps, max_usd, and
    # max_seconds (or is_exhausted for the deadline), plus a stuck run that
    # hits no_progress. Attach Trace and print its report for the step-budget
    # run so the behaviour in the README is visible.
    raise NotImplementedError


if __name__ == "__main__":
    raise SystemExit(main())
