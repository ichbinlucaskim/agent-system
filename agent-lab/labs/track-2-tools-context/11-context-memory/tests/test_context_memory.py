"""Tests for Lab 11 - Context and memory.

Budgeting, compaction, and the scratchpad are all deterministic local logic
and are tested offline. The scratchpad is pointed at a temporary directory so
no test touches the lab's data directory. The one test that involves a model
stubs it, because what is under test is which context reached it.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest


def _load(name: str, path: Path):
    """Load a module by file path.

    The module is registered in sys.modules before execution because
    dataclasses look their own module up by name while being created.
    """
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


LAB_ROOT = Path(__file__).resolve().parents[1]
solution = _load("lab11_solution", LAB_ROOT / "solution" / "main.py")


def _message(role: str, content: str, *, anchor: bool = False, tier: str | None = None) -> dict:
    message: dict = {"role": role, "content": content}
    if anchor:
        message["anchor"] = True
    if tier is not None:
        message["tier"] = tier
    return message


def _text_block(text: str) -> SimpleNamespace:
    return SimpleNamespace(type="text", text=text)


def _tool_use_block(block_id: str, name: str, arguments: dict) -> SimpleNamespace:
    return SimpleNamespace(type="tool_use", id=block_id, name=name, input=arguments)


def test_budget_messages_never_drops_an_anchor():
    """An anchor survives even when the estimate still exceeds the limit."""
    anchor = _message("user", "task statement " * 50, anchor=True)
    filler = _message("user", "chatter " * 50)
    kept = solution.budget_messages([anchor, filler], limit=1)
    assert anchor in kept
    assert filler not in kept


def test_budget_messages_drops_the_oldest_first():
    """The surviving non-anchor messages of one tier are the most recent."""
    messages = [_message("user", f"turn {i} " + "x" * 40) for i in range(6)]
    per_message = solution._message_tokens(messages[0])
    kept = solution.budget_messages(messages, limit=per_message * 3)
    assert kept == messages[-len(kept):]
    assert len(kept) < len(messages)


def test_budget_messages_leaves_a_fitting_list_untouched():
    """A list already under the limit comes back unchanged."""
    messages = [_message("user", "short"), _message("assistant", "reply")]
    assert solution.budget_messages(messages, limit=10_000) == messages


def test_budget_messages_sacrifices_raw_turns_before_the_digest():
    """The digest outlives chit-chat, because it holds more per token.

    Dropping strictly by age inverts this: the digest is always the oldest
    non-anchor message, so it goes first and the identifiers, decisions, and
    constraints that compaction preserved are thrown away to keep small talk.
    """
    digest = _message("user", "Summary: ORDER-42 must ship. " * 4, tier=solution.TIER_DIGEST)
    chatter = [_message("user", f"nice weather number {i} " * 4) for i in range(4)]

    # Room for the digest and about one chat turn.
    limit = solution._message_tokens(digest) + solution._message_tokens(chatter[0]) + 1
    kept = solution.budget_messages([digest] + chatter, limit=limit)

    assert digest in kept
    assert len(kept) < len(chatter) + 1


def test_budget_messages_can_still_drop_a_digest_when_nothing_else_is_left():
    """The digest is protected relative to turns, not absolutely."""
    digest = _message("user", "Summary: " + "x" * 400, tier=solution.TIER_DIGEST)
    kept = solution.budget_messages([digest], limit=5)
    assert kept == []


def test_budget_messages_does_not_make_an_unknown_tier_immortal():
    """A message with a tier this code does not know is still droppable.

    Otherwise a typo in a tier name silently pins a message in the window,
    which is a leak that only shows up as a rising bill.
    """
    typo = _message("user", "x" * 400, tier="digset")
    assert solution.budget_messages([typo], limit=5) == []


def test_compact_keeps_recent_turns_verbatim():
    """The last keep_recent messages appear unmodified in the output."""
    messages = [
        _message("user", "The staging site is SITE-204, agreed with the docs team."),
        _message("assistant", "Noted, using SITE-204 and it must not change."),
        _message("user", "recent question one"),
        _message("assistant", "recent answer one"),
    ]
    compacted = solution.compact(messages, keep_recent=2)
    assert compacted[-2:] == messages[-2:]
    # The older turns collapsed into a single summary message.
    assert len(compacted) == 3
    assert "SITE-204" in compacted[0]["content"]
    assert compacted[0]["tier"] == solution.TIER_DIGEST


def test_compaction_never_costs_more_than_the_turns_it_replaced():
    """Compaction that grows the context is not compaction.

    Keeping whole sentences means a history where nearly every sentence
    carries an identifier compacts to something longer than the original, so
    the digest needs a cap rather than a hope.
    """
    dense = [
        _message("user", f"Order ORDER-{i} must ship before the deadline and cannot be delayed.")
        for i in range(8)
    ]
    assert solution.total_tokens(solution.compact(dense)) <= solution.total_tokens(dense)

    # A history too small to be worth summarising at all: the digest's own
    # preamble costs more than the turn it would replace, so capping the facts
    # is not enough and compaction has to be declined outright.
    tiny = [_message("user", "ORDER-1 must go."), _message("user", "ok")]
    assert solution.compact(tiny, keep_recent=1) == tiny


def test_compact_respects_an_explicit_target():
    """A digest asked to fit a target does not exceed it."""
    dense = [
        _message("user", f"Order ORDER-{i} must ship before the deadline and cannot be delayed.")
        for i in range(10)
    ]
    compacted = solution.compact(dense, keep_recent=2, target=20)
    digest = compacted[0]
    assert digest["tier"] == solution.TIER_DIGEST
    assert solution._message_tokens(digest) <= 20


def test_scratchpad_round_trips_a_note(tmp_path):
    """A note written and read back returns the same content."""
    scratchpad = solution.Scratchpad(tmp_path)
    content = "SITE-204 content diff: 3 pages changed."
    scratchpad.write("content-findings", content)
    assert scratchpad.read("content-findings") == content
    assert scratchpad.list() == ["content-findings"]


def test_a_pointer_names_the_note_its_size_and_how_to_read_it(tmp_path):
    """The pointer has to be actionable, not a label.

    A pointer that does not say how to fetch the note leaves the third tier a
    dead end, and one that does not say how big it is gives the model no way
    to judge whether fetching it is worth the tokens.
    """
    scratchpad = solution.Scratchpad(tmp_path)
    body = "detail " * 40
    pointer = scratchpad.write("findings", body)
    assert "findings" in pointer
    assert str(solution.estimate_tokens(body)) in pointer
    assert solution.READ_NOTE_TOOL["name"] in pointer


def test_scratchpad_rejects_a_path_that_escapes_its_directory(tmp_path):
    """A name containing .. raises instead of writing outside the directory."""
    scratchpad = solution.Scratchpad(tmp_path)
    with pytest.raises(ValueError):
        scratchpad.write("../escape", "should never land on disk")
    assert list(tmp_path.parent.glob("escape*")) == []


def test_build_context_stays_within_the_limit(tmp_path):
    """The assembled context fits the limit when the anchors alone fit."""
    anchors = [_message("user", "Constraint: launch before 2026-09-01.")]
    history = [
        _message("user", f"turn {i}: " + "filler text about nothing much " * 5)
        for i in range(10)
    ]
    scratchpad = solution.Scratchpad(tmp_path)
    scratchpad.write("notes", "bulk detail lives here, not in the window")

    limit = 120
    context = solution.build_context(anchors, history, scratchpad, limit)
    estimate = solution.total_tokens(context)
    assert estimate <= limit
    # The anchor is still present after trimming.
    assert any(message.get("anchor") for message in context)


def test_build_context_keeps_note_bodies_out_of_the_window(tmp_path):
    """Only the pointer goes in, which is the whole point of the third tier.

    Without this, a build_context that inlined every note body would pass as
    long as it happened to fit, and the tier would exist in name only.
    """
    scratchpad = solution.Scratchpad(tmp_path)
    body = "UNIQUEBODYMARKER " + "column level detail " * 30
    scratchpad.write("findings", body)

    context = solution.build_context(
        [_message("user", "Constraint: launch before 2026-09-01.")],
        [_message("user", "what is left?")],
        scratchpad,
        limit=400,
    )
    joined = " ".join(str(message["content"]) for message in context)
    assert "UNIQUEBODYMARKER" not in joined
    assert "findings" in joined


def test_build_context_does_not_compact_a_history_that_already_fits(tmp_path):
    """Compaction is lossy, so a fitting history is left alone."""
    scratchpad = solution.Scratchpad(tmp_path)
    # Genuinely compressible: most of each turn is prose that compaction would
    # discard, so the test would notice compaction happening.
    history = [
        _message(
            "user",
            "We talked at length about naming and tooling and none of it "
            f"mattered much in the end. Decision {i}: ORDER-{i} must ship.",
        )
        for i in range(10)
    ]
    assert solution.total_tokens(solution.compact(history)) < solution.total_tokens(history)

    context = solution.build_context([], history, scratchpad, limit=10_000)
    assert history == [message for message in context if message in history]
    assert not any("Summary of" in str(message["content"]) for message in context)


def test_api_messages_drop_the_budgeters_bookkeeping():
    """anchor and tier are ours, not the API's, and must come off."""
    context = [
        _message("user", "hello", anchor=True),
        _message("assistant", "hi", tier=solution.TIER_TURN),
    ]
    for message in solution.to_api_messages(context):
        assert set(message) == {"role", "content"}


def test_api_messages_merge_the_gap_a_dropped_turn_leaves():
    """Dropping an assistant turn leaves two user turns in a row.

    That is the budgeter's doing, so normalising it belongs with the
    budgeter rather than in a retry after the API complains.
    """
    context = [
        _message("user", "first"),
        _message("user", "second"),
        _message("assistant", "reply"),
    ]
    merged = solution.to_api_messages(context)
    assert [message["role"] for message in merged] == ["user", "assistant"]
    assert "first" in merged[0]["content"] and "second" in merged[0]["content"]


def test_api_messages_do_not_start_with_an_assistant_turn():
    """Dropping the first user turn can leave the list starting mid-reply."""
    context = [_message("assistant", "orphaned reply"), _message("user", "question")]
    normalised = solution.to_api_messages(context)
    assert normalised[0]["role"] == "user"
    assert "orphaned" not in normalised[0]["content"]


def test_read_note_reports_a_bad_name_with_the_real_options(tmp_path):
    """A note name from a model is a guess, so the error names the options."""
    scratchpad = solution.Scratchpad(tmp_path)
    scratchpad.write("findings", "detail")
    text, failed = solution.run_read_note(scratchpad, {"name": "no-such-note"})
    assert failed is True
    assert "findings" in text


def test_the_model_can_follow_a_pointer_to_detail_left_out_of_the_window(tmp_path, monkeypatch):
    """The third tier is reachable, so bulk detail is out but not lost.

    The model is stubbed because what is under test is the plumbing: that the
    note body was absent from the context, that read_note fetched it, and that
    the fetched text reached the model.
    """
    scratchpad = solution.Scratchpad(tmp_path)
    scratchpad.write("findings", "The onboarding page is missing a translation.")

    seen: list[list[dict]] = []

    def fake_complete_with_tools(messages, tools, **kwargs):
        # A snapshot, because the caller keeps appending to the same list.
        seen.append(list(messages))
        assert tools == [solution.READ_NOTE_TOOL]
        if len(seen) == 1:
            return SimpleNamespace(
                stop_reason="tool_use",
                content=[_tool_use_block("tu_1", "read_note", {"name": "findings"})],
            )
        return SimpleNamespace(
            stop_reason="end_turn",
            content=[_text_block("The onboarding page.")],
        )

    monkeypatch.setattr(solution, "complete_with_tools", fake_complete_with_tools)

    context = solution.build_context(
        [_message("user", "Answer from this conversation and the scratchpad.")],
        [_message("user", "Which page is missing a translation?")],
        scratchpad,
        limit=400,
    )
    answer, read = solution.answer_with_scratchpad(context, scratchpad)

    assert answer == "The onboarding page."
    assert read == ["findings"]
    # The body was never in the window; it arrived as a tool result.
    first_turn = " ".join(str(message["content"]) for message in seen[0])
    assert "missing a translation." not in first_turn
    results = [
        block
        for message in seen[-1]
        if isinstance(message.get("content"), list)
        for block in message["content"]
        if isinstance(block, dict) and block.get("type") == "tool_result"
    ]
    assert len(results) == 1
    assert "onboarding" in results[0]["content"]


def test_an_empty_answer_reports_why_instead_of_looking_like_a_bad_one():
    """A refusal is not a context failure, and must not read like one.

    An empty string scored against a checklist looks exactly like a context
    that was trimmed too hard, which sends you tuning the budget to fix
    something the budget did not cause.
    """
    refused = SimpleNamespace(stop_reason="refusal", content=[])
    reported = solution._text_or_reason(refused)
    assert "refusal" in reported
