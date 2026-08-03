"""Tests for Lab 10 - An MCP-style server.

The protocol handlers are pure functions tested offline, and the round trip
test starts the real server as a subprocess over stdio. Nothing here needs an
API key or the network.
"""

from __future__ import annotations

import importlib.util
import io
import json
import sys
from pathlib import Path


def _load(name: str, path: Path):
    """Load a module by file path.

    The module is registered in sys.modules before execution because
    dataclasses look their own module up by name while being created.
    """
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


LAB_ROOT = Path(__file__).resolve().parents[1]
solution = _load("lab10_solution", LAB_ROOT / "solution" / "main.py")


def test_list_tools_returns_two_valid_definitions():
    """Both tools carry a name, a description, and an object input_schema."""
    tools = solution.list_tools()
    assert len(tools) == 2
    for tool in tools:
        assert tool["name"]
        assert tool["description"]
        assert tool["input_schema"]["type"] == "object"


def test_handle_request_echoes_the_request_id():
    """The response id matches the request id, so replies can be matched."""
    response = solution.handle_request(
        {"jsonrpc": "2.0", "id": 42, "method": "tools/list"}
    )
    assert response["id"] == 42
    assert "result" in response


def test_an_unknown_method_returns_jsonrpc_error_32601():
    """An unknown method is a -32601 error object, not a result."""
    response = solution.handle_request(
        {"jsonrpc": "2.0", "id": 7, "method": "tools/destroy"}
    )
    assert response["error"]["code"] == -32601
    assert "result" not in response


def test_a_malformed_line_does_not_kill_the_server():
    """Invalid JSON answers with -32700 and the loop keeps reading."""
    stdin = io.StringIO(
        "this is not json\n"
        + json.dumps({"jsonrpc": "2.0", "id": 1, "method": "tools/list"})
        + "\n"
    )
    stdout = io.StringIO()
    solution.serve(stdin, stdout)
    responses = [json.loads(line) for line in stdout.getvalue().splitlines()]
    assert len(responses) == 2
    assert responses[0]["error"]["code"] == -32700
    # The request after the bad line was still served.
    assert responses[1]["id"] == 1
    assert "result" in responses[1]


def test_a_failing_tool_returns_an_error_result_not_an_exception():
    """Bad arguments come back as is_error True naming the valid input."""
    result = solution.call_tool("get_stock_level", {"sku": "SKU-999"})
    assert result["is_error"] is True
    assert "SKU-100" in result["content"]

    missing = solution.call_tool("get_stock_level", {})
    assert missing["is_error"] is True
    assert "sku" in missing["content"]


def test_a_subprocess_round_trip_lists_and_calls_a_tool():
    """A real subprocess answers tools/list and tools/call, then shuts down."""
    client = solution.MCPClient(timeout_s=10.0)
    client.start()
    try:
        tools = client.list_tools()
        assert {tool["name"] for tool in tools} == {
            "get_stock_level",
            "get_shipping_days",
        }
        result = client.call("get_stock_level", {"sku": "SKU-300"})
        assert result["is_error"] is False
        assert "47" in result["content"]
    finally:
        client.close()
    # After close the server process is gone; poll() reports an exit code.
    assert client._process is None
