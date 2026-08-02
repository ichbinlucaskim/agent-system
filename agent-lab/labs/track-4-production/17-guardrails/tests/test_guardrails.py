"""Tests for Lab 17 - Guardrails.

Each test names the behaviour the lab must produce and describes its
assertion in a comment. The bodies skip until the lab is implemented:
replace the skip with the real assertion as you build each piece.
"""

from __future__ import annotations

import pytest


def test_oversized_input_is_rejected_with_a_reason():
    # Assert input past the length cap returns ok False and a reason naming the limit.
    pytest.skip("Lab not implemented yet")


def test_an_out_of_scope_request_is_rejected_in_code():
    # Assert the refusal happens in check_input, without a model call.
    pytest.skip("Lab not implemented yet")


def test_validate_output_reports_every_violation():
    # Assert a payload with a missing field and a wrong type returns both errors, not just the first.
    pytest.skip("Lab not implemented yet")


def test_wrap_untrusted_names_its_source():
    # Assert the wrapper contains the source label and the data-not-instructions rule.
    pytest.skip("Lab not implemented yet")


def test_detect_injection_flags_a_known_phrasing():
    # Assert content containing 'ignore previous instructions' is flagged.
    pytest.skip("Lab not implemented yet")


def test_detect_injection_does_not_flag_ordinary_text():
    # Assert a normal document returns no flags, since a noisy detector gets switched off.
    pytest.skip("Lab not implemented yet")


def test_guarded_answer_reports_its_guardrail_decisions():
    # Assert the result lists the guardrails that ran, so a refusal is explainable.
    pytest.skip("Lab not implemented yet")
