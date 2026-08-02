"""Tests for Lab 14 - Human in the loop.

Each test names the behaviour the lab must produce and describes its
assertion in a comment. The bodies skip until the lab is implemented:
replace the skip with the real assertion as you build each piece.
"""

from __future__ import annotations

import pytest


def test_a_forbidden_action_is_never_executed():
    # Assert the executor is not called and the approver is not prompted for a forbidden tool.
    pytest.skip("Lab not implemented yet")


def test_an_unknown_tool_defaults_to_confirm():
    # Assert a tool missing from POLICY is classified 'confirm' rather than 'auto'.
    pytest.skip("Lab not implemented yet")


def test_an_auto_action_runs_without_an_approver():
    # Assert an auto-classified action executes even when the approver would deny.
    pytest.skip("Lab not implemented yet")


def test_a_denied_confirmation_does_not_execute():
    # Assert an approver returning False leaves the action unexecuted and records the reason.
    pytest.skip("Lab not implemented yet")


def test_the_diff_shows_added_and_removed_lines():
    # Assert render_diff includes both the removed line and the added line for a changed file.
    pytest.skip("Lab not implemented yet")


def test_every_path_returns_an_audit_record():
    # Assert refusals, approvals, and denials all return a record naming the classification.
    pytest.skip("Lab not implemented yet")
