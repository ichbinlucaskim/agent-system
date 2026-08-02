"""Tests for Lab 03 - Routing.

Each test names the behaviour the lab must produce and describes its
assertion in a comment. The bodies skip until the lab is implemented:
replace the skip with the real assertion as you build each piece.
"""

from __future__ import annotations

import pytest


def test_classify_returns_a_known_route():
    # Assert the returned label is a key of ROUTES for a clearly on-topic question.
    pytest.skip("Lab not implemented yet")


def test_an_unrecognised_label_falls_back_to_other():
    # Assert that when the model returns a label outside ROUTES, classify returns 'other' instead of propagating it.
    pytest.skip("Lab not implemented yet")


def test_handle_uses_the_prompt_for_the_named_route():
    # Assert an unknown route name is handled by the 'other' prompt rather than raising.
    pytest.skip("Lab not implemented yet")


def test_route_and_answer_reports_the_route_taken():
    # Assert the result dict carries both route and answer, so the decision is loggable.
    pytest.skip("Lab not implemented yet")


def test_misroute_rate_matches_a_hand_counted_example():
    # Assert that a labelled set with two known disagreements out of ten returns 0.2, and that an empty set returns 0.0.
    pytest.skip("Lab not implemented yet")
