"""Tests for Lab 16 - Observability.

Each test names the behaviour the lab must produce and describes its
assertion in a comment. The bodies skip until the lab is implemented:
replace the skip with the real assertion as you build each piece.
"""

from __future__ import annotations

import pytest


def test_each_step_is_recorded_exactly_once():
    # Assert a run of three steps produces three records, in call order.
    pytest.skip("Lab not implemented yet")


def test_a_failing_step_is_still_recorded():
    # Assert a step that raises appears in the trace with its error text and its duration.
    pytest.skip("Lab not implemented yet")


def test_per_step_costs_sum_to_the_run_total():
    # Assert the sum of attributed costs equals the cost computed from the summed usage, within a small tolerance.
    pytest.skip("Lab not implemented yet")


def test_slowest_and_costliest_can_be_different_steps():
    # Assert a trace where the slow step is cheap ranks them differently.
    pytest.skip("Lab not implemented yet")


def test_the_report_names_every_step():
    # Assert every step name appears in the rendered report, so nothing is silently missing.
    pytest.skip("Lab not implemented yet")
