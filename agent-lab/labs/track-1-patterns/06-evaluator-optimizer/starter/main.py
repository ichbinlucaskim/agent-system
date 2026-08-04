"""Lab 06 - Evaluator and optimizer (starter).

Goal: Pair a generator call with a critic call in a loop, define explicit stopping criteria, bound the loop with a maximum iteration budget, and return the best draft rather than the last one.

Fill in each function below. Every one carries a TODO describing what to
do and which step of the README it maps to. Run the tests with:

    pytest labs/track-1-patterns/06-evaluator-optimizer/tests -v
"""

from __future__ import annotations

from typing import Any

# TODO: step 1. The checks the evaluator grades against, one string each.
# Each has to be decidable on its own: "stays under 150 words" can be passed
# or failed, "is well written" cannot. Vague criteria are the usual reason
# this pattern fails, because the score they produce carries no information.
CRITERIA: list[str] = []


def generate(task: str, feedback: str | None = None, previous: str | None = None) -> str:
    """Produce a draft, optionally revising the previous one from critique."""
    # TODO: step 2. When feedback is present, include it as an explicit instruction, together with the previous draft it criticises. A loop whose second call cannot see the critique is only resampling, and one that sees the critique but not the draft has to rewrite from scratch and loses criteria it had already met.
    raise NotImplementedError


def evaluate(task: str, draft: str) -> dict[str, Any]:
    """Score a draft against CRITERIA and explain what is wrong."""
    # TODO: step 3. Return {'score': int, 'passed': bool, 'feedback': str}. Ask for JSON and parse it rather than reading a number out of prose.
    raise NotImplementedError


def is_done(evaluation: dict[str, Any], iteration: int, *, max_iterations: int, target_score: int) -> tuple[bool, str]:
    """Decide whether the loop should stop, and say why."""
    # TODO: step 4. Two exits: the score clears target_score, or iteration reaches max_iterations. Return the reason so the caller can tell success from exhaustion.
    raise NotImplementedError


def refine(task: str, *, max_iterations: int = 3, target_score: int = 8) -> dict[str, Any]:
    """Run the generate and evaluate loop under a fixed budget."""
    # TODO: step 5. Thread both the feedback and the draft it criticises forward into the next generation, track the best draft seen rather than the last one, and return {'draft', 'score', 'iteration', 'stop_reason', 'history'}.
    raise NotImplementedError


def main() -> int:
    """Run the lab end to end and print what happened."""
    # TODO: final step. Wire the functions above together and print
    # enough that the behaviour described in the README is visible.
    raise NotImplementedError


if __name__ == "__main__":
    raise SystemExit(main())
