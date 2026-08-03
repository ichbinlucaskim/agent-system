"""Lab 11 - Context and memory (reference solution).

The context window treated as a budget: estimate token cost, drop or compact
history under a limit while protecting anchors, and keep bulk detail in a
scratchpad on disk with only a pointer in the window.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

# Sentences worth keeping through compaction: identifiers like SKU-100 or
# ORDER-42, and the language of decisions and constraints.
_IDENTIFIER = re.compile(r"\b[A-Z][A-Z0-9]*-\d+\b|\b\d{2,}\b")
_DECISION = re.compile(
    r"\b(must|never|always|cannot|decided|agreed|deadline|limit|require[sd]?)\b",
    re.IGNORECASE,
)


def estimate_tokens(text: str) -> int:
    """Rough character-based token estimate. Not a billing number.

    English text averages roughly four characters per token, which is close
    enough for drop-or-keep decisions. When a number needs to be exact,
    count tokens with the API instead of estimating them.
    """
    return (len(text) + 3) // 4


def _message_tokens(message: dict[str, Any]) -> int:
    """Estimate one message's cost from its content."""
    return estimate_tokens(str(message.get("content", "")))


def budget_messages(messages: list[dict[str, Any]], limit: int) -> list[dict[str, Any]]:
    """Drop oldest-first until the estimate fits, protecting anchors."""
    kept = list(messages)
    while sum(_message_tokens(message) for message in kept) > limit:
        for index, message in enumerate(kept):
            if not message.get("anchor"):
                del kept[index]
                break
        else:
            # Only anchors remain. Exceeding the limit is the lesser failure:
            # silently dropping the system prompt or the task statement looks
            # like the model getting worse for no reason.
            break
    return kept


def compact(messages: list[dict[str, Any]], *, keep_recent: int = 4) -> list[dict[str, Any]]:
    """Summarise older turns and keep recent ones verbatim."""
    if keep_recent <= 0:
        older, recent = list(messages), []
    elif len(messages) <= keep_recent:
        return list(messages)
    else:
        older, recent = messages[:-keep_recent], messages[-keep_recent:]

    # Compaction is lossy on purpose. What survives is what a later step
    # would otherwise have to ask about again: identifiers, decisions, and
    # constraints, not prose.
    facts: list[str] = []
    for message in older:
        content = str(message.get("content", ""))
        for sentence in re.split(r"(?<=[.?])\s+", content):
            sentence = sentence.strip()
            if sentence and (_IDENTIFIER.search(sentence) or _DECISION.search(sentence)):
                facts.append(sentence)

    body = " ".join(facts) if facts else "No identifiers, decisions, or constraints."
    summary = {
        "role": "user",
        "content": f"Summary of {len(older)} earlier turns: {body}",
    }
    return [summary] + list(recent)


class Scratchpad:
    """Notes on disk, with only a pointer kept in the window."""

    def __init__(self, directory: str | Path | None = None) -> None:
        if directory is None:
            directory = Path(__file__).resolve().parents[1] / "data"
        self._directory = Path(directory)
        self._directory.mkdir(parents=True, exist_ok=True)

    def _path(self, name: str) -> Path:
        # A note name can come from a model, so it is untrusted input. Only
        # a plain filename is accepted; anything that could climb out of the
        # data directory is rejected.
        if ".." in name or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]*", name):
            raise ValueError(
                f"invalid note name {name!r}: use letters, digits, dot, "
                "dash, and underscore only"
            )
        return self._directory / f"{name}.txt"

    def write(self, name: str, content: str) -> str:
        """Store one note and return the pointer line for the window."""
        self._path(name).write_text(content, encoding="utf-8")
        # The pointer, not the body, is what goes in the window.
        return f"note {name!r} ({estimate_tokens(content)} tokens) is in the scratchpad"

    def read(self, name: str) -> str:
        """Return the full content of one note."""
        return self._path(name).read_text(encoding="utf-8")

    def list(self) -> list[str]:
        """Return the names of every stored note, sorted."""
        return sorted(path.stem for path in self._directory.glob("*.txt"))


def build_context(
    anchors: list[dict[str, Any]],
    history: list[dict[str, Any]],
    scratchpad: Any,
    limit: int,
) -> list[dict[str, Any]]:
    """Assemble the final message list within the token limit."""
    anchored = [{**message, "anchor": True} for message in anchors]
    compacted = compact(history)

    pointers: list[dict[str, Any]] = []
    notes = scratchpad.list()
    if notes:
        lines = "\n".join(f"- note {name!r} is in the scratchpad" for name in notes)
        pointers = [{"role": "user", "content": f"Scratchpad index:\n{lines}"}]

    # Anchors, then the summary, then recent turns, then the pointers. The
    # budgeter trims whatever still does not fit, oldest non-anchor first.
    return budget_messages(anchored + compacted + pointers, limit)


def main() -> int:
    """Run one conversation through the budget, offline."""
    anchors = [
        {
            "role": "user",
            "content": (
                "You are helping migrate the billing service. Constraint: "
                "the cutover must finish before 2026-09-01."
            ),
        }
    ]
    history = [
        {
            "role": "user",
            "content": (
                "Quick recap of where we are. We spent most of yesterday going "
                "back and forth about naming, tooling, and whose team owns "
                "what, and honestly a lot of that was noise. The one thing "
                "that matters: the staging database is DB-204."
            ),
        },
        {
            "role": "assistant",
            "content": (
                "Noted. I will target DB-204 for the dry run and ignore the "
                "rest of the naming discussion unless it becomes relevant."
            ),
        },
        {
            "role": "user",
            "content": (
                "Also, after a long thread with the platform folks, we decided "
                "to keep the old API frozen during the migration. Lots of "
                "opinions were aired but that was the conclusion."
            ),
        },
        {"role": "assistant", "content": "Understood, the old API must not change."},
        {"role": "user", "content": "The weather here is lovely today, by the way."},
        {"role": "assistant", "content": "Good to hear. Back to the migration when you are ready."},
        {"role": "user", "content": "What is left before the dry run?"},
        {"role": "assistant", "content": "Schema checks on DB-204, then the frozen API contract tests."},
    ]

    raw = anchors + history
    raw_tokens = sum(_message_tokens(message) for message in raw)
    print(f"raw context      {len(raw)} messages, ~{raw_tokens} tokens")

    scratchpad = Scratchpad()
    pointer = scratchpad.write(
        "schema-findings",
        "DB-204 schema diff: 3 tables changed, 1 index missing on invoices. "
        "Full column-level diff recorded during the dry run.",
    )
    print(f"scratchpad       {pointer}")

    # A limit the raw history exceeds but the compacted context fits: the
    # saving in this demo comes from compaction, not from dropping turns.
    limit = 185
    context = build_context(anchors, history, scratchpad, limit)
    context_tokens = sum(_message_tokens(message) for message in context)
    print(f"budgeted context {len(context)} messages, ~{context_tokens} tokens (limit {limit})\n")

    for message in context:
        marker = "*" if message.get("anchor") else " "
        print(f" {marker} {message['role']:<9} {str(message['content'])[:64]}")
    print("\nmessages marked * are anchors and are never dropped")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
