"""Lab 13 - Subagents (starter).

Goal: Delegate a bounded task to a child agent that has its own context
window and a restricted tool set, and compare a single-agent run against a
subagent run on the same task to see what delegation actually costs and buys.

Fill in each function below. Every one carries a TODO describing what to
do and which step of the README it maps to. Run the tests with:

    pytest labs/track-3-autonomy/13-subagents/tests -v
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

DEFAULT_MAX_STEPS = 6

# TODO: step 1. A small NOTES corpus the tools will read and write.
NOTES: dict[str, str] = {}

# TODO: step 1. Parent tool set must include a write tool (write_note) plus
# read tools. Children in the demo will be allowed only the read tools —
# capability is granted by construction, not by instruction.
ALL_TOOLS: list[dict[str, Any]] = []


@dataclass(frozen=True)
class SubagentSpec:
    """The definition of one child agent: prompt, tools, subtask, and budget."""

    # TODO: step 1. name, system, allowed_tools (names only), task (this
    # child's own subtask), and max_steps. Keeping tools as names forces
    # restrict_tools to resolve them against the parent's real set.
    name: str = ""
    system: str = ""
    allowed_tools: list[str] | None = None
    task: str = ""
    max_steps: int = DEFAULT_MAX_STEPS


def restrict_tools(
    all_tools: list[dict[str, Any]], allowed: list[str]
) -> list[dict[str, Any]]:
    """Return only the tool definitions a spec is allowed to use."""
    # TODO: step 2. Raise on a name the parent does not have, rather than
    # silently returning fewer tools. A typo that quietly removes a tool is
    # very hard to debug.
    raise NotImplementedError


def run_subagent(
    spec: Any,
    all_tools: list[dict[str, Any]],
    *,
    model_call: Callable[..., Any] | None = None,
    executor: Callable[[str, dict[str, Any]], tuple[str, bool]] | None = None,
) -> dict[str, Any]:
    """Run one child agent with its own context and restricted tools."""
    # TODO: step 3. Start from an empty message list carrying only spec.task.
    # Use a lab-12-shaped loop: step budget, feed tool results back, return a
    # named stop_reason. Passing any parent history defeats the pattern.
    raise NotImplementedError


def single_agent(
    task: str,
    all_tools: list[dict[str, Any]],
    *,
    model_call: Callable[..., Any] | None = None,
    executor: Callable[[str, dict[str, Any]], tuple[str, bool]] | None = None,
) -> dict[str, Any]:
    """Baseline: one agent, all tools, no delegation."""
    # TODO: step 4. This is the control in the experiment. Keep it honest:
    # same parent task, same model, same step-budget shape.
    raise NotImplementedError


def with_subagents(
    task: str,
    specs: list[Any],
    all_tools: list[dict[str, Any]],
    *,
    model_call: Callable[..., Any] | None = None,
    executor: Callable[[str, dict[str, Any]], tuple[str, bool]] | None = None,
) -> dict[str, Any]:
    """Fan out to subagents and let the parent read only the reports."""
    # TODO: step 5. Run the subagents concurrently. Each child uses spec.task.
    # The parent briefing must contain reports only — never child transcripts
    # or note bodies the children read.
    raise NotImplementedError


def compare(
    task: str,
    specs: list[Any],
    all_tools: list[dict[str, Any]],
    *,
    model_call: Callable[..., Any] | None = None,
    executor: Callable[[str, dict[str, Any]], tuple[str, bool]] | None = None,
) -> dict[str, Any]:
    """Run both approaches and report tokens, time, and answers."""
    # TODO: step 6. Return both runs side by side with total_tokens, steps,
    # seconds (> 0 when work happened), and answers. This lab ends in a
    # measurement, not an opinion.
    raise NotImplementedError


def main() -> int:
    """Run the lab end to end and print what happened."""
    # TODO: final step. Build read-only child specs (no write_note), run
    # compare, and print steps / tokens / seconds / answers for both sides.
    raise NotImplementedError


if __name__ == "__main__":
    raise SystemExit(main())
