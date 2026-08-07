"""Lab 17 - Guardrails (starter).

Goal: Defend an agent at its boundaries: filter what comes in, validate what
goes out against a schema, treat tool results as untrusted data rather than
instructions, and refuse out-of-scope requests in code rather than by asking
the model nicely.

Fill in each function below. Every one carries a TODO describing what to
do and which step of the README it maps to. Run the tests with:

    pytest labs/track-4-production/17-guardrails/tests -v
"""

from __future__ import annotations

from typing import Any, Callable

# TODO: step 1. Cap input length; list SCOPE_KEYWORDS for the allowed topics.
MAX_INPUT_CHARS = 2_000
SCOPE_KEYWORDS: frozenset[str] = frozenset()

# TODO: step 4. Known instruction-like phrasings for the tripwire.
INJECTION_PATTERNS: list[str] = []

# TODO: step 6. Documents stand in for tool results; one should embed an
# injection. Parent tools may include write_note; tools while reading must not.
DOCUMENTS: dict[str, str] = {}
PARENT_TOOLS: list[dict[str, Any]] = []
TOOLS_WHILE_READING: list[dict[str, Any]] = []

ANSWER_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "answer": {"type": "string"},
        "confidence": {"type": "number"},
    },
    "required": ["answer", "confidence"],
}


def check_input(text: str) -> tuple[bool, str]:
    """Filter an incoming request before it costs a model call."""
    # TODO: step 1. Empty, oversize, and out-of-scope each return (False, reason).
    raise NotImplementedError


def validate_output(payload: Any, schema: dict[str, Any]) -> tuple[bool, list[str]]:
    """Validate a parsed payload against a small schema."""
    # TODO: step 2. Collect every violation. Treat bool as not a number/integer
    # (bool subclasses int in Python).
    raise NotImplementedError


def wrap_untrusted(source: str, content: str) -> str:
    """Label tool output as data that is never an instruction."""
    # TODO: step 3. Name the source and state the data-not-instructions rule.
    raise NotImplementedError


def detect_injection(content: str) -> list[str]:
    """Flag instruction-like patterns inside untrusted content."""
    # TODO: step 4. Return matched patterns. Docstring: tripwire, not a wall.
    raise NotImplementedError


def tools_while_reading_untrusted() -> list[dict[str, Any]]:
    """Tool set exposed while untrusted content is in context."""
    # TODO: step 6. Must not include write_note. Prefer an empty list here.
    raise NotImplementedError


def guarded_answer(
    question: str,
    *,
    model_call: Callable[[list[dict[str, Any]], str, list[dict[str, Any]]], str]
    | None = None,
) -> dict[str, Any]:
    """Answer a question with every guardrail applied."""
    # TODO: step 5. Filter input; record tool_restriction; wrap docs; run
    # tripwire as FLAG-only (do not abort); call model_call(messages, system,
    # tools); validate output; return {'answer', 'guardrails': [...]} (and
    # optionally 'raw'). Withhold answer when schema fails.
    raise NotImplementedError


def main() -> int:
    """Run the lab end to end and print what happened."""
    # TODO: final step. Show each guardrail offline, including parent vs
    # while-reading tools, then one guarded_answer with a stub model_call.
    raise NotImplementedError


if __name__ == "__main__":
    raise SystemExit(main())
