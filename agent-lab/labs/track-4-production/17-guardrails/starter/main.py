"""Lab 17 - Guardrails (starter).

Goal: Defend an agent at its boundaries: filter what comes in, validate what goes out against a schema, treat tool results as untrusted data rather than instructions, and refuse out-of-scope requests in code rather than by asking the model nicely.

Fill in each function below. Every one carries a TODO describing what to
do and which step of the README it maps to. Run the tests with:

    pytest labs/track-4-production/17-guardrails/tests -v
"""

from __future__ import annotations

from typing import Any


def check_input(text: str) -> tuple[bool, str]:
    """Filter an incoming request before it costs a model call."""
    # TODO: step 1. Enforce a length cap and an allowed-topic check. Return the reason so a rejection can be explained, not just applied.
    raise NotImplementedError


def validate_output(payload: Any, schema: dict[str, Any]) -> tuple[bool, list[str]]:
    """Validate a parsed payload against a small schema."""
    # TODO: step 2. Return every violation, not just the first. A caller fixing one field at a time needs several round trips.
    raise NotImplementedError


def wrap_untrusted(source: str, content: str) -> str:
    """Label tool output as data that is never an instruction."""
    # TODO: step 3. Name the source and state the rule inside the wrapper. If the prompt does not distinguish data from instructions, the model cannot either.
    raise NotImplementedError


def detect_injection(content: str) -> list[str]:
    """Flag instruction-like patterns inside untrusted content."""
    # TODO: step 4. Return the patterns matched. Document in the docstring that this is a tripwire, not a defence: the real control is the restricted tool set.
    raise NotImplementedError


def guarded_answer(question: str) -> dict[str, Any]:
    """Answer a question with every guardrail applied."""
    # TODO: step 5. Filter, wrap tool results, validate the output, and return {'answer', 'guardrails': [...]} so each decision is visible and auditable.
    raise NotImplementedError


def main() -> int:
    """Run the lab end to end and print what happened."""
    # TODO: final step. Wire the functions above together and print
    # enough that the behaviour described in the README is visible.
    raise NotImplementedError


if __name__ == "__main__":
    raise SystemExit(main())
