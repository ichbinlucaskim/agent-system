"""Lab 11 - Context and memory (starter).

Goal: Treat the context window as a budget you manage: estimate token cost, drop or compact history under a limit while protecting anchors, move bulk detail to a scratchpad file the model can still reach, and decide deliberately what stays in the window and what stays out.

Fill in each function below. Every one carries a TODO describing what to
do and which step of the README it maps to. Run the tests with:

    pytest labs/track-2-tools-context/11-context-memory/tests -v
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

# TODO: step 3. A raw conversational turn, and the digest that replaced older
# turns. Pointers into the scratchpad ride in the digest tier too.
TIER_TURN = "turn"
TIER_DIGEST = "digest"

# TODO: step 2. What gets sacrificed first when the budget is tight. Dropping
# strictly by age puts the digest first, because it is always the oldest
# non-anchor message, which throws away everything compaction preserved in
# order to keep chit-chat.
DROP_ORDER: tuple[str, ...] = ()

# Fields the budgeter uses for bookkeeping. They are ours, not the API's.
_BOOKKEEPING = ("anchor", "tier")


def estimate_tokens(text: str) -> int:
    """Rough character-based token estimate. Not a billing number."""
    # TODO: step 1. Divide the character count by a constant. Document in the docstring that this is for drop-or-keep decisions only, and that exact counts come from the API.
    raise NotImplementedError


def total_tokens(messages: list[dict[str, Any]]) -> int:
    """Estimate the cost of a whole message list."""
    raise NotImplementedError


def budget_messages(messages: list[dict[str, Any]], limit: int) -> list[dict[str, Any]]:
    """Drop by tier, oldest first within a tier, protecting anchors."""
    # TODO: step 2. A message marked anchor is never dropped, even if that
    # means exceeding the limit: silently dropping the system prompt looks
    # like the model getting worse for no reason. Everything else goes in
    # DROP_ORDER, oldest first within a tier, so the digest outlives the raw
    # turns it was built from. Finish with a pass that can drop any remaining
    # non-anchor message, or a typo in a tier name pins a message in the
    # window forever and shows up only as a rising bill.
    raise NotImplementedError


def compact(
    messages: list[dict[str, Any]],
    *,
    keep_recent: int = 4,
    target: int | None = None,
) -> list[dict[str, Any]]:
    """Summarise older turns into a digest and keep recent ones verbatim."""
    # TODO: step 3. Compaction is lossy on purpose: preserve identifiers,
    # decisions, and constraints, not prose. Tag the digest with TIER_DIGEST
    # and return it followed by the untouched recent turns. Cap its size: a
    # history where nearly every sentence carries an identifier otherwise
    # compacts to something longer than it replaced, so a digest needs a
    # budget rather than a hope. If it cannot beat what it replaced, do not
    # compact at all.
    raise NotImplementedError


class Scratchpad:
    """Notes on disk, with only a pointer kept in the window."""

    # TODO: step 4. Implement write, read, list, and pointer under a data
    # directory. Reject a note name that escapes the directory: a path from a
    # model is untrusted input. The pointer must name the note, say how big it
    # is, and say how to read it, or the model has no way to judge whether
    # opening it is worth the tokens and no way to open it at all.


def scratchpad_index(scratchpad: Any) -> list[dict[str, Any]]:
    """Return the pointer message for every stored note, or nothing."""
    # TODO: step 4. One message listing every note's pointer, tagged
    # TIER_DIGEST: a handful of tokens is the only route to everything
    # deliberately left out of the window.
    raise NotImplementedError


def build_context(
    anchors: list[dict[str, Any]],
    history: list[dict[str, Any]],
    scratchpad: Any,
    limit: int,
) -> list[dict[str, Any]]:
    """Assemble the final message list within the token limit."""
    # TODO: step 5. Anchors, then the digest, then recent turns, then the
    # scratchpad pointers, trimmed to the limit. Skip compaction entirely when
    # the raw history already fits: it is lossy, so paying for it without
    # pressure is pure loss. Give the digest a target computed from what is
    # left after the tiers that cannot be compressed.
    raise NotImplementedError


def to_api_messages(messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Turn a budgeted context into something the Messages API accepts."""
    # TODO: step 6. Strip the bookkeeping fields. Then fix the two shapes
    # budgeting creates: dropping an assistant turn from between two user
    # turns leaves two user messages in a row, and dropping the first user
    # turn can leave the list starting with an assistant message. Both are the
    # budgeter's doing, so they get fixed here rather than in a retry after
    # the API complains.
    raise NotImplementedError


READ_NOTE_TOOL: dict[str, Any] = {}
# TODO: step 6. One tool that reads a note by name. Describe when to call it,
# as lab 07 taught, and say that the context holds only pointers so the detail
# is unavailable until it is read.


def run_read_note(scratchpad: Any, arguments: dict[str, Any]) -> tuple[str, bool]:
    """Execute read_note and return its text plus whether it failed."""
    # TODO: step 6. A note name from a model is a guess, so a bad name comes
    # back as an error result naming the real options, not as an exception.
    raise NotImplementedError


def answer_with_scratchpad(
    context: list[dict[str, Any]],
    scratchpad: Any,
    *,
    max_tool_rounds: int = 3,
) -> tuple[str, list[str]]:
    """Answer from a budgeted context, letting the model follow pointers."""
    # TODO: step 6. Run the agentic loop with READ_NOTE_TOOL so the model can
    # open the notes it decides it needs. Without this the pointers are a dead
    # end and the third tier exists in name only. Return the answer and which
    # notes were actually read. If the answer is empty, report the stop_reason
    # rather than an empty string: a refusal is not a context failure, and
    # reading it as one sends you tuning the budget to fix something else.
    raise NotImplementedError


def main() -> int:
    """Compare ways of filling the window, by cost and by answer."""
    # TODO: step 7. Ask one question whose answer needs a fact from early
    # history and a fact that only lives in a note, then answer it from three
    # contexts: everything in the window, a trim by age alone, and the
    # budgeted context with pointers. Print the token cost and whether each
    # answer actually contains the two facts. Comparing token counts alone
    # tells you the budget shrank, not whether the answer survived.
    raise NotImplementedError


if __name__ == "__main__":
    raise SystemExit(main())
