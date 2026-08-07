"""Lab 11 - Context and memory (reference solution).

The context window treated as a budget: estimate token cost, drop or compact
history under a limit while protecting anchors, and keep bulk detail in a
scratchpad on disk with only a pointer in the window.

Two rules shape the whole file. Cutting has to happen in order of value, not
in order of age, because the compressed tiers hold more per token than the raw
turns that follow them. And a pointer is only useful if something can follow
it, so the model gets a tool that reads the note.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from common.client import (
    MissingAPIKeyError,
    complete,
    complete_with_tools,
    text_of,
    tool_uses,
)

# Sentences worth keeping through compaction: identifiers like SKU-100 or
# ORDER-42, and the language of decisions and constraints.
_IDENTIFIER = re.compile(r"\b[A-Z][A-Z0-9]*-\d+\b|\b\d{2,}\b")
_DECISION = re.compile(
    r"\b(must|never|always|cannot|decided|agreed|deadline|limit|require[sd]?)\b",
    re.IGNORECASE,
)

# A raw conversational turn, and the compressed tiers: the digest that replaced
# older turns, and the pointers into the scratchpad.
TIER_TURN = "turn"
TIER_DIGEST = "digest"

# What gets sacrificed first when the budget is tight. Raw turns go before the
# digest because the digest is what survived compaction: identifiers,
# decisions, and constraints, at a fraction of the tokens. Dropping strictly by
# age inverts this and throws the digest away to keep chit-chat, which is the
# single easiest way to make a budgeter actively harmful.
DROP_ORDER: tuple[str, ...] = (TIER_TURN, TIER_DIGEST)

# Fields the budgeter uses for bookkeeping. They are ours, not the API's, and
# have to come off before a message is sent.
_BOOKKEEPING = ("anchor", "tier")


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


def total_tokens(messages: list[dict[str, Any]]) -> int:
    """Estimate the cost of a whole message list."""
    return sum(_message_tokens(message) for message in messages)


def _tier(message: dict[str, Any]) -> str:
    """Return the sacrifice tier of one message."""
    return str(message.get("tier", TIER_TURN))


def budget_messages(messages: list[dict[str, Any]], limit: int) -> list[dict[str, Any]]:
    """Drop by tier, oldest first within a tier, protecting anchors."""
    over = total_tokens(messages) - limit
    if over <= 0:
        return list(messages)

    def sacrifice_order(entry: tuple[int, dict[str, Any]]) -> tuple[int, int]:
        """Rank one message by what it costs to lose: tier first, then age."""
        index, message = entry
        tier = _tier(message)
        # A tier this function does not recognise sorts last rather than
        # being skipped, so a typo in a tier name cannot pin a message in the
        # window forever.
        rank = DROP_ORDER.index(tier) if tier in DROP_ORDER else len(DROP_ORDER)
        return rank, index

    # Raw turns before the compressed tiers, oldest first within a tier. The
    # whole policy is this sort key, so it is worth reading as one.
    droppable = sorted(
        ((index, message) for index, message in enumerate(messages) if not message.get("anchor")),
        key=sacrifice_order,
    )

    doomed: set[int] = set()
    for index, message in droppable:
        if over <= 0:
            break
        doomed.add(index)
        over -= _message_tokens(message)

    # If the anchors alone exceed the limit, exceeding it is the lesser
    # failure: silently dropping the system prompt or the task statement looks
    # like the model getting worse for no reason.
    return [message for index, message in enumerate(messages) if index not in doomed]


def compact(
    messages: list[dict[str, Any]],
    *,
    keep_recent: int = 4,
    target: int | None = None,
) -> list[dict[str, Any]]:
    """Summarise older turns into a digest and keep recent ones verbatim."""
    if keep_recent <= 0:
        older, recent = list(messages), []
    elif len(messages) <= keep_recent:
        return list(messages)
    else:
        older, recent = messages[:-keep_recent], messages[-keep_recent:]

    if not older:
        return list(recent)

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

    # A digest has a budget too. Keeping whole sentences means a history where
    # every sentence carries an identifier compacts to something longer than
    # it replaced, so the size has to be capped rather than hoped for.
    replaced = total_tokens(older)
    ceiling = replaced if target is None else min(target, replaced)
    prefix = f"Summary of {len(older)} earlier turns: "

    def digest_tokens(kept_facts: list[str]) -> int:
        return estimate_tokens(prefix + " ".join(kept_facts))

    # Oldest facts go first, which is a real cost: an early constraint can be
    # squeezed out by later ones. Anything that must never be squeezed out
    # belongs in the anchors, not in the history.
    while facts and digest_tokens(facts) > ceiling:
        facts.pop(0)

    body = " ".join(facts) if facts else "No identifiers, decisions, or constraints."
    digest = {"role": "user", "content": prefix + body, "tier": TIER_DIGEST}

    if _message_tokens(digest) >= replaced:
        # Compaction that saves nothing is pure loss. Leave the turns alone.
        return list(messages)
    return [digest] + list(recent)


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
        return self.pointer(name)

    def read(self, name: str) -> str:
        """Return the full content of one note."""
        return self._path(name).read_text(encoding="utf-8")

    def list(self) -> list[str]:
        """Return the names of every stored note, sorted."""
        return sorted(path.stem for path in self._directory.glob("*.txt"))

    def pointer(self, name: str) -> str:
        """Return the one-line pointer that stands in for a note."""
        # The size is part of the pointer because it is what lets the model
        # judge whether reading the note is worth the tokens, and naming the
        # tool is what makes the pointer actionable rather than trivia.
        size = estimate_tokens(self.read(name))
        return f"- {name} (~{size} tokens), read with read_note"


def scratchpad_index(scratchpad: Any) -> list[dict[str, Any]]:
    """Return the pointer message for every stored note, or nothing."""
    names = scratchpad.list()
    if not names:
        return []
    lines = "\n".join(scratchpad.pointer(name) for name in names)
    return [
        {
            "role": "user",
            "content": f"Scratchpad notes (bodies are not in this context):\n{lines}",
            # Pointers ride in the compressed tier for the same reason the
            # digest does: a handful of tokens is the only route to everything
            # deliberately left out of the window.
            "tier": TIER_DIGEST,
        }
    ]


def build_context(
    anchors: list[dict[str, Any]],
    history: list[dict[str, Any]],
    scratchpad: Any,
    limit: int,
) -> list[dict[str, Any]]:
    """Assemble the final message list within the token limit."""
    anchored = [{**message, "anchor": True} for message in anchors]
    pointers = scratchpad_index(scratchpad)

    raw = anchored + list(history) + pointers
    if total_tokens(raw) <= limit:
        # Compaction is lossy, so it is not worth paying for when the whole
        # history already fits. Budgeting is a response to pressure, not a
        # ritual to perform every turn.
        return raw

    # The digest gets what is left after the tiers that cannot be compressed,
    # and only half of that, so the recent turns it sits beside still fit.
    room = limit - total_tokens(anchored + pointers)
    compacted = compact(history, target=max(room // 2, 1))
    return budget_messages(anchored + compacted + pointers, limit)


def to_api_messages(messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Turn a budgeted context into something the Messages API accepts.

    Budgeting breaks the shape the API expects in two ways that are easy to
    miss offline. Dropping an assistant turn from between two user turns
    leaves two user messages in a row, and dropping the first user turn can
    leave the list starting with an assistant message. Both are the
    budgeter's doing, so normalising them belongs here rather than in a
    retry after the API complains.
    """
    normalised: list[dict[str, Any]] = []
    for message in messages:
        clean = {key: value for key, value in message.items() if key not in _BOOKKEEPING}
        if not normalised and clean.get("role") != "user":
            continue
        if normalised and normalised[-1]["role"] == clean.get("role"):
            previous = normalised[-1]
            if isinstance(previous["content"], str) and isinstance(clean.get("content"), str):
                previous["content"] = f"{previous['content']}\n\n{clean['content']}"
                continue
        normalised.append(clean)
    return normalised


READ_NOTE_TOOL: dict[str, Any] = {
    "name": "read_note",
    "description": (
        "Read the full text of one scratchpad note. Call this whenever the "
        "context lists a note whose detail you need in order to answer. The "
        "context carries only note names and sizes, never the note bodies, "
        "so the detail is unavailable until you read it."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "name": {
                "type": "string",
                "description": "The note name exactly as listed in the scratchpad index.",
            }
        },
        "required": ["name"],
    },
}


def run_read_note(scratchpad: Any, arguments: dict[str, Any]) -> tuple[str, bool]:
    """Execute read_note and return its text plus whether it failed."""
    name = str(arguments.get("name", ""))
    try:
        return scratchpad.read(name), False
    except (ValueError, FileNotFoundError, OSError):
        # A note name from a model is a guess. The error names the real
        # options so the guess can be corrected on the next turn.
        available = ", ".join(scratchpad.list()) or "none"
        return f"Error: no note named {name!r}. Available notes: {available}.", True


def _text_or_reason(response: Any) -> str:
    """Return the response text, or an explanation of why there is none."""
    text = text_of(response)
    if text.strip():
        return text
    # An empty answer is not the same as a bad answer. A refusal, or a run
    # that ended on max_tokens, has nothing to do with what was in the
    # window, and reading it as a context failure sends you tuning the budget
    # to fix something the budget did not cause.
    return f"[no text returned, stop_reason={response.stop_reason}]"


def answer_plainly(context: list[dict[str, Any]]) -> str:
    """Answer from the window alone, with no way to reach the scratchpad."""
    return _text_or_reason(complete(to_api_messages(context)))


def answer_with_scratchpad(
    context: list[dict[str, Any]],
    scratchpad: Any,
    *,
    max_tool_rounds: int = 3,
) -> tuple[str, list[str]]:
    """Answer from a budgeted context, letting the model follow pointers.

    This is what makes the third tier a tier rather than a dead end. Detail
    kept out of the window is still reachable, and the window only pays for
    the notes the model actually decides to open.
    """
    messages = to_api_messages(context)
    read: list[str] = []

    response = None
    for _ in range(max_tool_rounds):
        response = complete_with_tools(messages, [READ_NOTE_TOOL])
        messages.append({"role": "assistant", "content": response.content})
        if response.stop_reason != "tool_use":
            break
        results: list[dict[str, Any]] = []
        for block in tool_uses(response):
            text, failed = run_read_note(scratchpad, dict(block.input))
            if not failed:
                read.append(str(dict(block.input).get("name", "")))
            results.append(
                {
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": text,
                    "is_error": failed,
                }
            )
        messages.append({"role": "user", "content": results})

    return (_text_or_reason(response) if response is not None else ""), read


ANCHORS: list[dict[str, Any]] = [
    {
        "role": "user",
        "content": (
            "You are helping prepare the Q4 documentation launch. "
            "Constraint: the launch must ship before 2026-09-01. Answer only "
            "from this conversation and the scratchpad."
        ),
    }
]

HISTORY: list[dict[str, Any]] = [
    {
        "role": "user",
        "content": (
            "Quick recap of where we are. We spent most of yesterday going "
            "back and forth about naming, tooling, and whose team owns "
            "what, and honestly a lot of that was noise. The one thing "
            "that matters: the staging site is SITE-204."
        ),
    },
    {
        "role": "assistant",
        "content": (
            "Noted. I will use SITE-204 for the rehearsal and set the naming "
            "discussion aside unless it becomes relevant."
        ),
    },
    {
        "role": "user",
        "content": (
            "Also, after a long thread with the docs team, we decided the old "
            "pricing page must stay frozen during the launch. Lots of "
            "opinions were aired but that was the conclusion."
        ),
    },
    {
        "role": "assistant",
        "content": "Understood, the old pricing page must not change.",
    },
    {"role": "user", "content": "The weather here is lovely today, by the way."},
    {
        "role": "assistant",
        "content": "Good to hear. Back to the launch when you are ready.",
    },
    {"role": "user", "content": "What is left before the rehearsal?"},
    {
        "role": "assistant",
        "content": "Link checks on SITE-204, then the frozen pricing page review.",
    },
]

# The turns in HISTORY that carry nothing worth keeping. Nothing in the
# budgeter knows about these; they exist so the demo can point out that the
# surviving verbatim turns include pure chit-chat.
NOISE_MARKERS = ("weather", "Good to hear")

NOTE_NAME = "content-findings"
NOTE_BODY = (
    "SITE-204 content diff, recorded during the rehearsal.\n"
    "Three pages changed: onboarding, changelog, api-reference.\n"
    "One page is missing a translation: the onboarding page.\n"
    "Section-level detail: onboarding gained a quickstart section, changelog "
    "dropped its legacy entries, api-reference gained a versioning table. "
    "None of these changes are reversible once the launch starts, so the "
    "rehearsal has to confirm each one."
)

# The question needs one fact from early history and one from the note, so an
# answer can be scored rather than admired.
QUESTION = (
    "Two things: what did we decide about the old pricing page, and which "
    "page is missing a translation?"
)


def _verdict(answer: str) -> str:
    """Check the two facts the question actually asked for."""
    lowered = answer.lower()
    knows_page = (
        "frozen" in lowered or "must not change" in lowered or "unchanged" in lowered
    )
    knows_translation = "onboarding" in lowered
    return (
        f"pricing page frozen: {'yes' if knows_page else 'NO'}, "
        f"missing translation: {'onboarding' if knows_translation else 'NO'}"
    )


def main() -> int:
    """Compare three ways of filling the window, by cost and by answer."""
    scratchpad = Scratchpad()
    print(f"scratchpad       {scratchpad.write(NOTE_NAME, NOTE_BODY)}")

    ask = [{"role": "user", "content": QUESTION}]
    limit = 150
    # The incoming question is not something the budgeter may trim, so its
    # cost comes off the limit before any of the history is considered.
    room = limit - total_tokens(ask)

    # 1. Everything in the window. The most expensive option, and still short
    #    one answer, because the bulk detail was never in the conversation.
    raw = ANCHORS + HISTORY + ask

    # 2. Budgeting with no tiers: oldest first, no anchors, no compaction, no
    #    pointers. Cheap, and it eats the constraint along with the chit-chat.
    naive = list(ANCHORS + HISTORY)
    while naive and total_tokens(naive) > room:
        del naive[0]
    naive = naive + ask

    # 3. Anchors protected, older turns compacted, bulk detail behind a
    #    pointer the model can follow.
    budgeted = build_context(ANCHORS, HISTORY, scratchpad, room) + ask

    print(f"\nraw context      {len(raw):>2} messages, ~{total_tokens(raw):>3} tokens")
    print(f"naive trim       {len(naive):>2} messages, ~{total_tokens(naive):>3} tokens (limit {limit})")
    print(f"budgeted         {len(budgeted):>2} messages, ~{total_tokens(budgeted):>3} tokens (limit {limit})")

    print("\nwhat survived budgeting:")
    for message in budgeted:
        if message.get("anchor"):
            marker = "anchor "
        elif _tier(message) == TIER_DIGEST:
            marker = "digest "
        else:
            marker = "turn   "
        print(f"  {marker} {str(message['content'])[:62]}")

    # Recency is a cheap stand-in for relevance and it fails in a way worth
    # seeing: the weather turn is recent, so it survives verbatim, while the
    # migration decisions had to be squeezed into the digest to fit.
    kept_verbatim = [str(m["content"]) for m in budgeted if _tier(m) == TIER_TURN]
    if any(marker in text for text in kept_verbatim for marker in NOISE_MARKERS):
        print("\n  note: a chit-chat turn survived verbatim because it is recent,")
        print("  while the launch decisions had to be squeezed into the digest.")
        print("  Recency is not importance, and nothing here knows the difference.")

    print(f"\nquestion: {QUESTION}")
    print("  the answer needs one fact from early history and one from the note")
    try:
        # Only the budgeted context has a pointer, and only it gets the tool.
        # That is the architectural difference under test: a big window does
        # not help with detail that was never in the conversation.
        answers = [
            ("raw     ", answer_plainly(raw), ""),
            ("naive   ", answer_plainly(naive), ""),
        ]
        budgeted_answer, notes_read = answer_with_scratchpad(budgeted, scratchpad)
        answers.append(("budgeted", budgeted_answer, f", notes read: {notes_read or 'none'}"))

        for label, answer, extra in answers:
            print(f"\n  [{label}] {_verdict(answer)}{extra}")
            print(f"    {answer.strip()[:200]}")

        # Trimming by age does not merely shrink a context, it can produce one
        # that opens mid-thread with decisions already asserted, which is
        # indistinguishable from a planted history. The digest avoids this by
        # declaring what it stands in for; a vague "continuing our earlier
        # conversation" does not. Whether a given model refuses will change,
        # but the naive context is missing the constraint either way.
        if any("[no text returned" in answer for _, answer, _ in answers):
            print("\n  note: a variant returned no text at all. A stripped context can")
            print("  fail outright rather than just answer worse, so check stop_reason")
            print("  before blaming the budget for an empty answer.")
    except MissingAPIKeyError as exc:
        print(f"  skipped, needs a model: {exc}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
