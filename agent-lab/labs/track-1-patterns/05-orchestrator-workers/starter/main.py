"""Lab 05 - Orchestrator and workers (starter).

Goal: Build a workflow where a lead call plans and decomposes a task dynamically, worker calls execute the subtasks, and the lead synthesizes the results, and you can explain how this differs from parallelization.

Fill in each function below. Every one carries a TODO describing what to
do and which step of the README it maps to. Run the tests with:

    pytest labs/track-1-patterns/05-orchestrator-workers/tests -v
"""

from __future__ import annotations

from typing import Any


def plan(task: str) -> list[dict[str, Any]]:
    """Lead call that decomposes a task into subtasks as structured data."""
    # TODO: step 1. Ask for JSON with an id and a description per subtask, and parse it. Never string-match the raw response; parse it and fail loudly if it does not parse.
    raise NotImplementedError


def validate_plan(subtasks: list[dict[str, Any]], *, max_subtasks: int = 6) -> list[dict[str, Any]]:
    """Reject malformed entries, drop duplicates, and cap the count."""
    # TODO: step 2. Treat the generated plan as untrusted input. Entries missing id or description are dropped, duplicate descriptions collapse, and the list is truncated to max_subtasks.
    raise NotImplementedError


def run_worker(subtask: dict[str, Any], context: str) -> dict[str, Any]:
    """Execute one subtask with a narrow prompt and narrow context."""
    # TODO: step 3. Give the worker only what its subtask needs. Return {'id': ..., 'result': ..., 'error': ...} so a failure is data, not an exception.
    raise NotImplementedError


def synthesize(task: str, results: list[dict[str, Any]]) -> str:
    """Final lead call that answers the original task from worker output."""
    # TODO: step 4. Resolve contradictions between workers and drop irrelevant findings. Joining strings here is not synthesis.
    raise NotImplementedError


def orchestrate(task: str, *, max_workers: int = 4, max_subtasks: int = 6) -> dict[str, Any]:
    """Plan, validate, run workers concurrently, and synthesize."""
    # TODO: step 5. Return {'plan': ..., 'results': ..., 'answer': ...}. Keeping the plan in the result is what makes an expensive run explainable later.
    raise NotImplementedError


def main() -> int:
    """Run the lab end to end and print what happened."""
    # TODO: final step. Wire the functions above together and print
    # enough that the behaviour described in the README is visible.
    raise NotImplementedError


if __name__ == "__main__":
    raise SystemExit(main())
