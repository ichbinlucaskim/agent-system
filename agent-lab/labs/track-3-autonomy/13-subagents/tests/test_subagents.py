"""Tests for Lab 13 - Subagents.

Each test names the behaviour the lab must produce and describes its
assertion in a comment. The bodies skip until the lab is implemented:
replace the skip with the real assertion as you build each piece.
"""

from __future__ import annotations

import pytest


def test_restrict_tools_returns_only_the_allowed_tools():
    # Assert a spec allowing one tool yields exactly that tool definition.
    pytest.skip("Lab not implemented yet")


def test_restrict_tools_raises_on_a_tool_the_parent_lacks():
    # Assert an unknown tool name raises instead of silently returning a shorter list.
    pytest.skip("Lab not implemented yet")


def test_a_subagent_starts_with_no_parent_history():
    # Assert the message list the subagent is called with contains none of the parent's turns.
    pytest.skip("Lab not implemented yet")


def test_a_subagent_cannot_call_a_tool_outside_its_spec():
    # Assert a tool_use naming a restricted tool returns an error result rather than executing.
    pytest.skip("Lab not implemented yet")


def test_compare_reports_totals_for_both_approaches():
    # Assert the result carries token totals and elapsed time for the single-agent and subagent runs.
    pytest.skip("Lab not implemented yet")
