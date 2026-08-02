"""Lab 13 - Subagents (starter).

Goal: Delegate a bounded task to a child agent that has its own context window and a restricted tool set, and you can compare a single-agent run against a subagent run on the same task to see what delegation actually costs and buys.

Fill in each function below. Every one carries a TODO describing what to
do and which step of the README it maps to. Run the tests with:

    pytest labs/track-3-autonomy/13-subagents/tests -v
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


class SubagentSpec:
    """The definition of one child agent: prompt, tools, and budget."""

    # TODO: step 1. A dataclass with name, system, allowed_tools (names only), and max_steps. Keeping the tool list as names forces restrict_tools to resolve them against the parent's real set.


def restrict_tools(all_tools: list[dict[str, Any]], allowed: list[str]) -> list[dict[str, Any]]:
    """Return only the tool definitions a spec is allowed to use."""
    # TODO: step 2. Raise on a name the parent does not have, rather than silently returning fewer tools. A typo that quietly removes a tool is very hard to debug.
    raise NotImplementedError


def run_subagent(spec: Any, task: str, all_tools: list[dict[str, Any]]) -> dict[str, Any]:
    """Run one child agent with its own context and restricted tools."""
    # TODO: step 3. Start from an empty message list. Passing any parent history here defeats the entire point of the pattern.
    raise NotImplementedError


def single_agent(task: str, all_tools: list[dict[str, Any]]) -> dict[str, Any]:
    """Baseline: one agent, all tools, no delegation."""
    # TODO: step 4. This is the control in the experiment. Keep it honest: same task, same model, same budget shape.
    raise NotImplementedError


def with_subagents(task: str, specs: list[Any], all_tools: list[dict[str, Any]]) -> dict[str, Any]:
    """Fan out to subagents and let the parent read only the reports."""
    # TODO: step 5. Run the subagents concurrently. The parent sees reports, never the subagents' intermediate work.
    raise NotImplementedError


def compare(task: str, specs: list[Any], all_tools: list[dict[str, Any]]) -> dict[str, Any]:
    """Run both approaches and report tokens, time, and answers."""
    # TODO: step 6. Return both runs side by side. This lab ends in a measurement, not an opinion.
    raise NotImplementedError


def main() -> int:
    """Run the lab end to end and print what happened."""
    # TODO: final step. Wire the functions above together and print
    # enough that the behaviour described in the README is visible.
    raise NotImplementedError


if __name__ == "__main__":
    raise SystemExit(main())
