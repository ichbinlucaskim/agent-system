"""Lab 12 - The agent loop (starter).

Goal: Build an autonomous loop that runs until it is done or until a budget stops it: explicit stop conditions, a step budget, a cost ceiling, retries on tool error, and detection of a run that is no longer making progress.

Fill in each function below. Every one carries a TODO describing what to
do and which step of the README it maps to. Run the tests with:

    pytest labs/track-3-autonomy/12-agent-loop/tests -v
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


class AgentBudget:
    """Independent ceilings on steps, spend, and wall-clock time."""

    # TODO: step 1. A dataclass with max_steps, max_usd, and max_seconds. They fail differently, so keep them separate rather than collapsing them into one number.


def is_exhausted(budget: Any, state: Any) -> tuple[bool, str]:
    """Report whether any budget is spent, and which one."""
    # TODO: step 2. Return (True, 'max_steps') and so on. The caller needs the reason, not just the fact, to tell success from exhaustion.
    raise NotImplementedError


def run_tool_with_retry(name: str, arguments: dict[str, Any], *, attempts: int = 2) -> tuple[str, bool]:
    """Retry a failing tool, then hand the error to the model."""
    # TODO: step 3. After the last attempt, return (error_text, True) instead of raising. A retry is your decision; returning the error is the model's.
    raise NotImplementedError


def detect_no_progress(history: list[tuple[str, str]], *, window: int = 3) -> bool:
    """Detect a run repeating the same action and observation."""
    # TODO: step 4. Hash recent (action, observation) pairs and return True when the last window entries are identical. A stuck agent does not crash, it repeats.
    raise NotImplementedError


def agent_loop(task: str, *, budget: Any) -> dict[str, Any]:
    """Run the autonomous loop until done or stopped."""
    # TODO: step 5. Return {'answer', 'stop_reason', 'steps', 'usd', 'trace'}. Every exit path must set a stop_reason, including the successful one.
    raise NotImplementedError


def main() -> int:
    """Run the lab end to end and print what happened."""
    # TODO: final step. Wire the functions above together and print
    # enough that the behaviour described in the README is visible.
    raise NotImplementedError


if __name__ == "__main__":
    raise SystemExit(main())
