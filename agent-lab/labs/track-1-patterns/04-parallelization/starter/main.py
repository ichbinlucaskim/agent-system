"""Lab 04 - Parallelization (starter).

Goal: Run model calls concurrently in the two useful shapes: sectioning, which splits independent subtasks across calls, and voting, which runs the same task several times and aggregates the answers.

Fill in each function below. Every one carries a TODO describing what to
do and which step of the README it maps to. Run the tests with:

    pytest labs/track-1-patterns/04-parallelization/tests -v
"""

from __future__ import annotations

from typing import Any


def section(task: str) -> list[dict[str, str]]:
    """Split a task into independent aspects, each with its own instruction."""
    # TODO: step 1. Return a list of {'name': ..., 'instruction': ...}. The sections must be genuinely independent; anything order-dependent belongs in lab 02.
    raise NotImplementedError


def run_sections(sections: list[dict[str, str]], text: str) -> list[dict[str, Any]]:
    """Run one call per section concurrently, preserving input order."""
    # TODO: step 2. Use ThreadPoolExecutor. Map futures back to their index so the returned order matches sections, not completion order. Record a failed call as an error entry instead of dropping it.
    raise NotImplementedError


def merge_sections(results: list[dict[str, Any]]) -> str:
    """Combine section results into one labelled report."""
    # TODO: step 3. Keep each section under its own heading. Blending them into prose loses the reason for sectioning in the first place.
    raise NotImplementedError


def vote(question: str, n: int = 3) -> list[str]:
    """Run the same question n times concurrently and collect the answers."""
    # TODO: step 4. Normalise each answer before returning it, so trivial formatting differences do not read as disagreement.
    raise NotImplementedError


def majority(answers: list[str]) -> tuple[str, float]:
    """Return the modal answer and the fraction of votes that agreed."""
    # TODO: step 5. Break ties deterministically, for example by first appearance, so the same votes always give the same result. An empty list should return ('', 0.0).
    raise NotImplementedError


def main() -> int:
    """Run the lab end to end and print what happened."""
    # TODO: final step. Wire the functions above together and print
    # enough that the behaviour described in the README is visible.
    raise NotImplementedError


if __name__ == "__main__":
    raise SystemExit(main())
