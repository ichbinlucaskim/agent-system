"""Lab 11 - Context and memory (starter).

Goal: Treat the context window as a budget you manage: estimate token cost, drop or compact history under a limit while protecting anchors, move bulk detail to a scratchpad file, and decide deliberately what stays in the window and what stays out.

Fill in each function below. Every one carries a TODO describing what to
do and which step of the README it maps to. Run the tests with:

    pytest labs/track-2-tools-context/11-context-memory/tests -v
"""

from __future__ import annotations

from pathlib import Path
from typing import Any


def estimate_tokens(text: str) -> int:
    """Rough character-based token estimate. Not a billing number."""
    # TODO: step 1. Divide the character count by a constant. Document in the docstring that this is for drop-or-keep decisions only, and that exact counts come from the API.
    raise NotImplementedError


def budget_messages(messages: list[dict[str, Any]], limit: int) -> list[dict[str, Any]]:
    """Drop oldest-first until the estimate fits, protecting anchors."""
    # TODO: step 2. A message marked anchor is never dropped, even if that means exceeding the limit. Silently dropping the system prompt looks like the model getting worse for no reason.
    raise NotImplementedError


def compact(messages: list[dict[str, Any]], *, keep_recent: int = 4) -> list[dict[str, Any]]:
    """Summarise older turns and keep recent ones verbatim."""
    # TODO: step 3. Compaction is lossy on purpose: preserve identifiers, decisions, and constraints, not prose. Return the summary followed by the untouched recent turns.
    raise NotImplementedError


class Scratchpad:
    """Notes on disk, with only a pointer kept in the window."""

    # TODO: step 4. Implement write, read, and list under a data directory. Reject a note name that escapes the directory: a path from a model is untrusted input.


def build_context(anchors: list[dict[str, Any]], history: list[dict[str, Any]], scratchpad: Any, limit: int) -> list[dict[str, Any]]:
    """Assemble the final message list within the token limit."""
    # TODO: step 5. Anchors, then the compacted summary, then recent turns, then one-line scratchpad pointers. The pointer, not the note body, is what goes in the window.
    raise NotImplementedError


def main() -> int:
    """Run the lab end to end and print what happened."""
    # TODO: final step. Wire the functions above together and print
    # enough that the behaviour described in the README is visible.
    raise NotImplementedError


if __name__ == "__main__":
    raise SystemExit(main())
