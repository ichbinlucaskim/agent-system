"""Tests for Lab 12 - The agent loop.

Each test names the behaviour the lab must produce and describes its
assertion in a comment. The bodies skip until the lab is implemented:
replace the skip with the real assertion as you build each piece.
"""

from __future__ import annotations

import pytest


def test_the_loop_stops_at_the_step_budget():
    # Assert a model that always requests a tool stops after max_steps with that stop reason.
    pytest.skip("Lab not implemented yet")


def test_the_cost_ceiling_stops_a_run_before_the_step_budget():
    # Assert a run with high per-step spend stops on max_usd while steps remain.
    pytest.skip("Lab not implemented yet")


def test_run_tool_with_retry_retries_then_surrenders():
    # Assert a tool that always fails is attempted exactly `attempts` times and then returns an error result rather than raising.
    pytest.skip("Lab not implemented yet")


def test_run_tool_with_retry_returns_a_recovered_result():
    # Assert a tool that fails once then succeeds returns the success without an error flag.
    pytest.skip("Lab not implemented yet")


def test_detect_no_progress_flags_a_repeated_action():
    # Assert three identical action and observation pairs return True.
    pytest.skip("Lab not implemented yet")


def test_detect_no_progress_ignores_genuine_variety():
    # Assert differing actions return False, so a working run is not stopped.
    pytest.skip("Lab not implemented yet")


def test_every_exit_path_sets_a_stop_reason():
    # Assert the successful path also names its stop reason, so a caller never has to infer why a run ended.
    pytest.skip("Lab not implemented yet")
