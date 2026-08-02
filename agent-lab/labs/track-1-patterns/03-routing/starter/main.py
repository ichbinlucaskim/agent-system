"""Lab 03 - Routing (starter).

Goal: Classify an incoming request and dispatch it to one of several specialized prompts or models, provide a safe fallback route, and measure the misroute rate on a labelled set.

Fill in each function below. Every one carries a TODO describing what to
do and which step of the README it maps to. Run the tests with:

    pytest labs/track-1-patterns/03-routing/tests -v
"""

from __future__ import annotations

from typing import Any


def classify(question: str) -> str:
    """Return exactly one route name from ROUTES, falling back to 'other'."""
    # TODO: step 2. Call the model with the closed list of route names, strip the response, and validate it against ROUTES before returning.
    raise NotImplementedError


def handle(route: str, question: str) -> str:
    """Answer the question using the system prompt for the given route."""
    # TODO: step 3. Look the system prompt up in ROUTES and make one call. An unknown route should use the 'other' prompt rather than raise.
    raise NotImplementedError


def route_and_answer(question: str) -> dict[str, Any]:
    """Classify, dispatch, and report both the answer and the route taken."""
    # TODO: step 4. Return {'route': ..., 'answer': ...}. The route must be visible to callers, not buried inside the handler.
    raise NotImplementedError


def misroute_rate(labelled: list[tuple[str, str]]) -> float:
    """Fraction of labelled questions the classifier sends to the wrong route."""
    # TODO: step 5. Run classify over each pair and divide disagreements by total. An empty list should return 0.0 rather than divide by zero.
    raise NotImplementedError


def main() -> int:
    """Run the lab end to end and print what happened."""
    # TODO: final step. Wire the functions above together and print
    # enough that the behaviour described in the README is visible.
    raise NotImplementedError


if __name__ == "__main__":
    raise SystemExit(main())
