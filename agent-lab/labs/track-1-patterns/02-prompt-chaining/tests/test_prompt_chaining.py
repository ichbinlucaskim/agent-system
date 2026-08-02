"""Tests for Lab 02 - Prompt chaining.

Each test names the behaviour the lab must produce and describes its
assertion in a comment. The bodies skip until the lab is implemented:
replace the skip with the real assertion as you build each piece.
"""

from __future__ import annotations

import pytest


def test_gate_rejects_an_empty_requirement_list():
    # Assert gate_requirements([]) returns ok False with a reason mentioning that nothing was extracted.
    pytest.skip("Lab not implemented yet")


def test_gate_rejects_a_single_vague_requirement():
    # Assert a list like ['make it good'] fails the gate.
    pytest.skip("Lab not implemented yet")


def test_gate_accepts_a_well_formed_list():
    # Assert three specific, actionable requirements pass with ok True.
    pytest.skip("Lab not implemented yet")


def test_run_chain_returns_every_intermediate_output():
    # Assert the result dict carries requirements, draft, and final, so a failure can be inspected step by step.
    pytest.skip("Lab not implemented yet")


def test_run_chain_stops_when_the_gate_fails():
    # Assert stopped_at names the gate and that draft_spec was never reached.
    pytest.skip("Lab not implemented yet")


def test_run_chain_retries_the_failed_step_once():
    # Assert extract_requirements is called exactly twice when the first attempt fails the gate and max_retries is 1.
    pytest.skip("Lab not implemented yet")
