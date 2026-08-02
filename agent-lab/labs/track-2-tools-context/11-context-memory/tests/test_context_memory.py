"""Tests for Lab 11 - Context and memory.

Each test names the behaviour the lab must produce and describes its
assertion in a comment. The bodies skip until the lab is implemented:
replace the skip with the real assertion as you build each piece.
"""

from __future__ import annotations

import pytest


def test_budget_messages_never_drops_an_anchor():
    # Assert an anchor survives even when the total estimate still exceeds the limit.
    pytest.skip("Lab not implemented yet")


def test_budget_messages_drops_the_oldest_first():
    # Assert the surviving non-anchor messages are the most recent ones.
    pytest.skip("Lab not implemented yet")


def test_budget_messages_leaves_a_fitting_list_untouched():
    # Assert a message list already under the limit is returned unchanged.
    pytest.skip("Lab not implemented yet")


def test_compact_keeps_recent_turns_verbatim():
    # Assert the last keep_recent messages appear unmodified in the output.
    pytest.skip("Lab not implemented yet")


def test_scratchpad_round_trips_a_note():
    # Assert a note written and then read back returns the same content.
    pytest.skip("Lab not implemented yet")


def test_scratchpad_rejects_a_path_that_escapes_its_directory():
    # Assert a note name containing .. raises rather than writing outside the data directory.
    pytest.skip("Lab not implemented yet")


def test_build_context_stays_within_the_limit():
    # Assert the assembled context estimate is under the limit when the anchors alone fit.
    pytest.skip("Lab not implemented yet")
