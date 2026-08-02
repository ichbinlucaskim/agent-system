"""Tests for Lab 04 - Parallelization.

Each test names the behaviour the lab must produce and describes its
assertion in a comment. The bodies skip until the lab is implemented:
replace the skip with the real assertion as you build each piece.
"""

from __future__ import annotations

import pytest


def test_run_sections_preserves_input_order():
    # Assert that when a later section finishes first, the returned list is still in the original section order.
    pytest.skip("Lab not implemented yet")


def test_a_failed_section_does_not_lose_the_others():
    # Assert that one raising call yields an error entry in its slot while the other sections still return results.
    pytest.skip("Lab not implemented yet")


def test_majority_picks_the_modal_answer_and_reports_agreement():
    # Assert ['yes','yes','no'] returns ('yes', 2/3).
    pytest.skip("Lab not implemented yet")


def test_majority_breaks_ties_deterministically():
    # Assert ['a','b'] returns the same answer on repeated calls.
    pytest.skip("Lab not implemented yet")


def test_majority_handles_an_empty_vote_list():
    # Assert an empty list returns ('', 0.0) rather than raising.
    pytest.skip("Lab not implemented yet")


def test_merge_sections_keeps_every_section_labelled():
    # Assert each section name appears in the merged report.
    pytest.skip("Lab not implemented yet")
