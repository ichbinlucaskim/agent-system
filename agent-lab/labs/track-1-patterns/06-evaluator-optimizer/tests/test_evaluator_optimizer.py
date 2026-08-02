"""Tests for Lab 06 - Evaluator and optimizer.

Each test names the behaviour the lab must produce and describes its
assertion in a comment. The bodies skip until the lab is implemented:
replace the skip with the real assertion as you build each piece.
"""

from __future__ import annotations

import pytest


def test_is_done_stops_on_a_passing_score():
    # Assert a score at or above target_score returns True with a reason naming success.
    pytest.skip("Lab not implemented yet")


def test_is_done_stops_at_the_iteration_budget():
    # Assert the loop stops at max_iterations even when nothing has ever passed, with a reason naming exhaustion.
    pytest.skip("Lab not implemented yet")


def test_refine_returns_the_best_draft_not_the_last():
    # Assert that when scores go 5 then 9 then 6, the returned draft is the one that scored 9.
    pytest.skip("Lab not implemented yet")


def test_refine_threads_feedback_into_the_next_generation():
    # Assert the second call to generate receives the feedback produced by the first evaluation.
    pytest.skip("Lab not implemented yet")


def test_refine_records_the_score_history():
    # Assert history has one entry per iteration, so a plateau is visible after the fact.
    pytest.skip("Lab not implemented yet")
