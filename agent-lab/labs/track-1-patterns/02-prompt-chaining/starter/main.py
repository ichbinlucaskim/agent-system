"""Lab 02 - Prompt chaining (starter).

Goal: Decompose a task into a fixed sequence of model calls where each call consumes the previous output, place a programmatic gate between steps, and decide when chaining is worth its extra cost and latency.

Fill in each function below. Every one carries a TODO describing what to
do and which step of the README it maps to. Run the tests with:

    pytest labs/track-1-patterns/02-prompt-chaining/tests -v
"""

from __future__ import annotations

from typing import Any


def extract_requirements(brief: str) -> list[str]:
    """Turn a free-form brief into a list of short requirement strings."""
    # TODO: step 1. Call the model with a system prompt that asks for one requirement per line, then parse the response into a list.
    raise NotImplementedError


def gate_requirements(requirements: list[str]) -> tuple[bool, str]:
    """Deterministic check between step one and step two. Returns (ok, reason)."""
    # TODO: step 2. Reject an empty list, a single vague entry, and entries shorter than a few words. The reason string is what a human reads when the chain stops.
    raise NotImplementedError


def draft_spec(requirements: list[str]) -> str:
    """Draft a specification from the gated requirements only."""
    # TODO: step 3. Pass the requirement list, not the original brief. Each step should see only what it needs.
    raise NotImplementedError


def polish_spec(spec: str) -> str:
    """Rewrite the draft for clarity without adding requirements."""
    # TODO: step 4. Instruct the model to change wording only. Adding a requirement here would bypass the gate.
    raise NotImplementedError


def run_chain(brief: str, *, max_retries: int = 1) -> dict[str, Any]:
    """Run the full chain and return every intermediate output."""
    # TODO: step 5. Run the three steps in order, apply the gate after step one, retry the failed step up to max_retries, and return a dict with keys requirements, gate, draft, final, and stopped_at.
    raise NotImplementedError


def main() -> int:
    """Run the lab end to end and print what happened."""
    # TODO: final step. Wire the functions above together and print
    # enough that the behaviour described in the README is visible.
    raise NotImplementedError


if __name__ == "__main__":
    raise SystemExit(main())
