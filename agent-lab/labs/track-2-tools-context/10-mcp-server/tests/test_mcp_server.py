"""Tests for Lab 10 - An MCP-style server.

Each test names the behaviour the lab must produce and describes its
assertion in a comment. The bodies skip until the lab is implemented:
replace the skip with the real assertion as you build each piece.
"""

from __future__ import annotations

import pytest


def test_list_tools_returns_two_valid_definitions():
    # Assert both tools have a name, a description, and an input_schema of type object.
    pytest.skip("Lab not implemented yet")


def test_handle_request_echoes_the_request_id():
    # Assert the response id matches the request id, so a client can match replies to calls.
    pytest.skip("Lab not implemented yet")


def test_an_unknown_method_returns_jsonrpc_error_32601():
    # Assert the response carries an error object with code -32601 and no result field.
    pytest.skip("Lab not implemented yet")


def test_a_malformed_line_does_not_kill_the_server():
    # Assert invalid JSON produces a -32700 error response and the loop continues reading.
    pytest.skip("Lab not implemented yet")


def test_a_failing_tool_returns_an_error_result_not_an_exception():
    # Assert call_tool with bad arguments returns is_error True with a message naming the valid input.
    pytest.skip("Lab not implemented yet")


def test_a_subprocess_round_trip_lists_and_calls_a_tool():
    # Assert a real subprocess started by MCPClient answers tools/list and tools/call, and that close shuts it down cleanly.
    pytest.skip("Lab not implemented yet")
