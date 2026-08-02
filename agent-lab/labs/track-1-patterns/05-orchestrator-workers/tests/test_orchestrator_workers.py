"""Tests for Lab 05 - Orchestrator and workers.

Each test names the behaviour the lab must produce and describes its
assertion in a comment. The bodies skip until the lab is implemented:
replace the skip with the real assertion as you build each piece.
"""

from __future__ import annotations

import pytest


def test_validate_plan_drops_entries_missing_required_fields():
    # Assert a subtask without a description is removed rather than passed to a worker.
    pytest.skip("Lab not implemented yet")


def test_validate_plan_caps_the_subtask_count():
    # Assert a twenty entry plan is truncated to max_subtasks.
    pytest.skip("Lab not implemented yet")


def test_validate_plan_removes_duplicate_subtasks():
    # Assert two identical descriptions collapse to one, so the same work is not paid for twice.
    pytest.skip("Lab not implemented yet")


def test_orchestrate_returns_the_plan_with_the_answer():
    # Assert the result carries the plan, so an expensive run can be explained after the fact.
    pytest.skip("Lab not implemented yet")


def test_a_failing_worker_does_not_abort_the_run():
    # Assert one worker raising leaves an error entry for that subtask while synthesis still runs on the rest.
    pytest.skip("Lab not implemented yet")
