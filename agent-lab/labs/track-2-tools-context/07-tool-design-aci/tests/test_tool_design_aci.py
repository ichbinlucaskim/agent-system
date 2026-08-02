"""Tests for Lab 07 - Tool design and the agent-computer interface.

Each test names the behaviour the lab must produce and describes its
assertion in a comment. The bodies skip until the lab is implemented:
replace the skip with the real assertion as you build each piece.
"""

from __future__ import annotations

import pytest


def test_both_tool_definitions_are_structurally_valid():
    # Assert each tool has name, description, and an input_schema of type object with a properties dict.
    pytest.skip("Lab not implemented yet")


def test_the_good_description_states_a_trigger_condition():
    # Assert GOOD_TOOL's description contains a when-to-call clause, which VAGUE_TOOL's does not.
    pytest.skip("Lab not implemented yet")


def test_the_good_schema_constrains_its_inputs():
    # Assert the good schema uses an enum or a required list that the vague one lacks.
    pytest.skip("Lab not implemented yet")


def test_format_tool_error_lists_the_valid_options():
    # Assert the message contains every valid option, so the model can fix its own call.
    pytest.skip("Lab not implemented yet")


def test_selection_rate_matches_a_hand_counted_example():
    # Assert three matches out of four returns 0.75, and that an empty case list returns 0.0.
    pytest.skip("Lab not implemented yet")
