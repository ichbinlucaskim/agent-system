"""Tests for Lab 18 - Packaging and deployment.

Each test names the behaviour the lab must produce and describes its
assertion in a comment. The bodies skip until the lab is implemented:
replace the skip with the real assertion as you build each piece.
"""

from __future__ import annotations

import pytest


def test_load_config_names_the_missing_variable():
    # Assert a missing required environment variable raises an error naming that variable.
    pytest.skip("Lab not implemented yet")


def test_load_config_applies_defaults():
    # Assert optional settings fall back to documented defaults rather than None.
    pytest.skip("Lab not implemented yet")


def test_health_returns_200_without_an_api_key():
    # Assert /health responds 200 with no ANTHROPIC_API_KEY set, since it must not call the model.
    pytest.skip("Lab not implemented yet")


def test_malformed_json_returns_400():
    # Assert a POST with an invalid body returns 400 and a JSON error, not a traceback.
    pytest.skip("Lab not implemented yet")


def test_the_cli_returns_a_non_zero_exit_code_on_failure():
    # Assert run_cli returns non-zero when the core raises, so automation can detect it.
    pytest.skip("Lab not implemented yet")


def test_both_entry_points_call_the_same_core():
    # Assert the CLI and the handler both reach `answer`, so the two paths cannot drift.
    pytest.skip("Lab not implemented yet")
