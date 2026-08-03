"""Tests for Lab 11 - Context and memory.

Budgeting, compaction, and the scratchpad are all deterministic local logic
and are tested offline. The scratchpad is pointed at a temporary directory so
no test touches the lab's data directory.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

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


def _message(role: str, content: str, *, anchor: bool = False) -> dict:
    message: dict = {"role": role, "content": content}
    if anchor:
        message["anchor"] = True
    return message


def test_budget_messages_never_drops_an_anchor():
    """An anchor survives even when the estimate still exceeds the limit."""
    anchor = _message("user", "task statement " * 50, anchor=True)
    filler = _message("user", "chatter " * 50)
    kept = solution.budget_messages([anchor, filler], limit=1)
    assert anchor in kept
    assert filler not in kept


def test_budget_messages_drops_the_oldest_first():
    """The surviving non-anchor messages are the most recent ones."""
    messages = [_message("user", f"turn {i} " + "x" * 40) for i in range(6)]
    per_message = solution._message_tokens(messages[0])
    kept = solution.budget_messages(messages, limit=per_message * 3)
    assert kept == messages[-len(kept):]
    assert len(kept) < len(messages)


def test_budget_messages_leaves_a_fitting_list_untouched():
    """A list already under the limit comes back unchanged."""
    messages = [_message("user", "short"), _message("assistant", "reply")]
    assert solution.budget_messages(messages, limit=10_000) == messages


def test_compact_keeps_recent_turns_verbatim():
    """The last keep_recent messages appear unmodified in the output."""
    messages = [
        _message("user", "The staging database is DB-204."),
        _message("assistant", "Noted, targeting DB-204."),
        _message("user", "recent question one"),
        _message("assistant", "recent answer one"),
    ]
    compacted = solution.compact(messages, keep_recent=2)
    assert compacted[-2:] == messages[-2:]
    # The older turns collapsed into a single summary message.
    assert len(compacted) == 3
    assert "DB-204" in compacted[0]["content"]


def test_scratchpad_round_trips_a_note(tmp_path):
    """A note written and read back returns the same content."""
    scratchpad = solution.Scratchpad(tmp_path)
    content = "DB-204 schema diff: 3 tables changed."
    scratchpad.write("schema-findings", content)
    assert scratchpad.read("schema-findings") == content
    assert scratchpad.list() == ["schema-findings"]


def test_scratchpad_rejects_a_path_that_escapes_its_directory(tmp_path):
    """A name containing .. raises instead of writing outside the directory."""
    scratchpad = solution.Scratchpad(tmp_path)
    with pytest.raises(ValueError):
        scratchpad.write("../escape", "should never land on disk")
    assert list(tmp_path.parent.glob("escape*")) == []


def test_build_context_stays_within_the_limit(tmp_path):
    """The assembled context fits the limit when the anchors alone fit."""
    anchors = [_message("user", "Constraint: cutover before 2026-09-01.")]
    history = [
        _message("user", f"turn {i}: " + "filler text about nothing much " * 5)
        for i in range(10)
    ]
    scratchpad = solution.Scratchpad(tmp_path)
    scratchpad.write("notes", "bulk detail lives here, not in the window")

    limit = 120
    context = solution.build_context(anchors, history, scratchpad, limit)
    estimate = sum(solution._message_tokens(message) for message in context)
    assert estimate <= limit
    # The anchor is still present after trimming.
    assert any(message.get("anchor") for message in context)
