"""Tests for Lab 15 - Evaluation.

Each test names the behaviour the lab must produce and describes its
assertion in a comment. The bodies skip until the lab is implemented:
replace the skip with the real assertion as you build each piece.
"""

from __future__ import annotations

import pytest


def test_a_deterministic_check_reports_its_failure_reason():
    # Assert a failing check returns a reason string, not just False.
    pytest.skip("Lab not implemented yet")


def test_the_pass_rate_is_computed_across_runs():
    # Assert a case passing 2 of 4 runs reports 0.5 rather than the last run's verdict.
    pytest.skip("Lab not implemented yet")


def test_an_intermittent_case_is_marked_flaky():
    # Assert a pass rate strictly between 0 and 1 is labelled flaky in the report.
    pytest.skip("Lab not implemented yet")


def test_the_report_names_every_failing_case():
    # Assert each failing case id appears in the rendered report.
    pytest.skip("Lab not implemented yet")


def test_an_unparsable_judge_response_is_recorded_as_an_error():
    # Assert a malformed judge reply is an error entry, not a silent score of zero.
    pytest.skip("Lab not implemented yet")
