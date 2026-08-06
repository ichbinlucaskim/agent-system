"""Tests for Lab 10 - An MCP-style server.

The protocol handlers are pure functions tested offline, and the round trip
test starts the real server as a subprocess over stdio. Nothing here needs an
API key or the network.
"""

from __future__ import annotations

import importlib.util
import io
import json
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest


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
SOLUTION_PATH = LAB_ROOT / "solution" / "main.py"
solution = _load("lab10_solution", SOLUTION_PATH)

META = solution.META


def _params(**extra) -> dict:
    """Build request params carrying the required protocol metadata."""
    params = dict(extra)
    params["_meta"] = {
        f"{META}protocolVersion": solution.PROTOCOL_VERSION,
        f"{META}clientCapabilities": {},
    }
    return params


def _request(method: str, request_id: int = 1, **extra) -> dict:
    return {
        "jsonrpc": "2.0",
        "id": request_id,
        "method": method,
        "params": _params(**extra),
    }


def _text_block(text: str) -> SimpleNamespace:
    return SimpleNamespace(type="text", text=text)


def _tool_use_block(block_id: str, name: str, arguments: dict) -> SimpleNamespace:
    return SimpleNamespace(type="tool_use", id=block_id, name=name, input=arguments)


def test_list_tools_returns_two_valid_definitions():
    """Both tools carry a name, a description, and an object inputSchema."""
    tools = solution.list_tools()
    assert len(tools) == 2
    for tool in tools:
        assert tool["name"]
        assert tool["description"]
        # MCP spells this camelCase; the Messages API spells it snake_case.
        assert tool["inputSchema"]["type"] == "object"
        assert "input_schema" not in tool


def test_tools_are_listed_in_a_deterministic_order():
    """The same set of tools always comes back in the same order.

    A client can only cache the catalogue, and the model can only get prompt
    cache hits on it, if the order does not move between calls.
    """
    assert solution.list_tools() == solution.list_tools()
    names = [tool["name"] for tool in solution.list_tools()]
    assert names == sorted(names)


def test_handle_request_echoes_the_request_id():
    """The response id matches the request id, so replies can be matched."""
    response = solution.handle_request(_request("tools/list", request_id=42))
    assert response["id"] == 42
    assert "result" in response


def test_there_is_no_handshake_to_perform_first():
    """tools/call works as the very first request, and initialize is gone.

    The protocol is stateless: a request carries everything the server needs,
    which is what lets it be load balanced across instances. Nothing has to
    happen before it, and the old handshake is simply an unknown method now.
    """
    called = solution.handle_request(
        _request("tools/call", name="get_stock_level", arguments={"sku": "SKU-100"})
    )
    assert called["result"]["isError"] is False

    legacy = solution.handle_request(_request("initialize"))
    assert legacy["error"]["code"] == -32601


def test_discover_reports_the_versions_the_server_speaks():
    """server/discover replaces the handshake and is optional, not required."""
    response = solution.handle_request(_request("server/discover"))
    assert solution.PROTOCOL_VERSION in response["result"]["supportedVersions"]


def test_a_request_without_protocol_metadata_is_refused():
    """A missing required _meta field is -32602, not a served request.

    With no handshake there is no other moment to check the version, so a
    request that omits it has to be rejected. Serving it anyway means quietly
    answering a client that may speak a different protocol.
    """
    for field in ("protocolVersion", "clientCapabilities"):
        meta = _params()["_meta"]
        del meta[f"{META}{field}"]
        response = solution.handle_request(
            {"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {"_meta": meta}}
        )
        assert response["error"]["code"] == -32602, field
        assert field in response["error"]["message"]

    bare = solution.handle_request({"jsonrpc": "2.0", "id": 1, "method": "tools/list"})
    assert bare["error"]["code"] == -32602


def test_an_unsupported_protocol_version_is_refused_with_the_alternatives():
    """A version mismatch is -32022 and says what the server does support."""
    params = _params()
    params["_meta"][f"{META}protocolVersion"] = "1999-01-01"
    response = solution.handle_request(
        {"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": params}
    )
    assert response["error"]["code"] == -32022
    # Naming the supported versions is what lets a client retry instead of
    # only learning that it failed.
    assert response["error"]["data"]["supported"] == solution.SUPPORTED_VERSIONS


def test_every_result_identifies_the_server_and_its_kind():
    """Results carry resultType and serverInfo, since no handshake did."""
    for method in ("server/discover", "tools/list"):
        result = solution.handle_request(_request(method))["result"]
        assert result["resultType"] == "complete"
        assert result["_meta"][f"{META}serverInfo"] == solution.SERVER_INFO


def test_the_tool_list_carries_a_cache_hint():
    """tools/list says how long it stays valid and who may share it."""
    result = solution.handle_request(_request("tools/list"))["result"]
    assert result["ttlMs"] > 0
    assert result["cacheScope"] == "public"


def test_an_unknown_method_returns_jsonrpc_error_32601():
    """An unknown method is a -32601 error object, not a result."""
    response = solution.handle_request(_request("tools/destroy", request_id=7))
    assert response["error"]["code"] == -32601
    assert "result" not in response


def test_a_malformed_line_does_not_kill_the_server():
    """Invalid JSON answers with -32700 and the loop keeps reading."""
    stdin = io.StringIO(
        "this is not json\n" + json.dumps(_request("tools/list")) + "\n"
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
    """Bad arguments come back as isError True naming the valid input."""
    result = solution.call_tool("get_stock_level", {"sku": "SKU-999"})
    assert result["isError"] is True
    assert "SKU-100" in solution.text_of_content(result["content"])

    missing = solution.call_tool("get_stock_level", {})
    assert missing["isError"] is True
    assert "sku" in solution.text_of_content(missing["content"])


def test_a_tool_result_is_a_list_of_content_blocks():
    """Results are content blocks, not a bare string."""
    result = solution.call_tool("get_shipping_days", {"method": "express"})
    assert isinstance(result["content"], list)
    assert result["content"][0]["type"] == "text"


def test_mcp_definitions_are_translated_for_the_model_api():
    """The two tool shapes are close enough to look interchangeable.

    They are not: inputSchema is not input_schema, and MCP carries fields the
    Messages API rejects. Forwarding the definitions untouched is the mistake
    this translation exists to prevent.
    """
    translated = solution.to_messages_api_tools(solution.list_tools())
    for mcp_tool, api_tool in zip(solution.list_tools(), translated):
        assert api_tool["input_schema"] == mcp_tool["inputSchema"]
        assert set(api_tool) == {"name", "description", "input_schema"}


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
        assert result["isError"] is False
        assert "47" in solution.text_of_content(result["content"])
    finally:
        client.close()
    # After close the server process is gone; poll() reports an exit code.
    assert client._process is None


def test_the_client_reuses_the_cached_tool_list():
    """A second list_tools within the advertised ttl does not hit the wire.

    The server is killed after the first call, so a cached answer is the only
    way the second one can succeed.
    """
    client = solution.MCPClient(timeout_s=5.0)
    client.start()
    try:
        first = client.list_tools()
        client._process.kill()
        client._process.wait()
        assert client.list_tools() == first
    finally:
        client.close()


def test_the_server_writes_nothing_but_protocol_to_stdout():
    """Every line on stdout parses as JSON, even after a malformed request.

    A stray print in the server is the classic way an stdio protocol breaks:
    the server keeps working, and the client dies decoding the greeting. The
    only place diagnostics can go is stderr.
    """
    requests = [
        json.dumps(_request("server/discover", request_id=1)),
        "not json at all",
        json.dumps(_request("tools/list", request_id=2)),
    ]
    completed = subprocess.run(
        [sys.executable, str(SOLUTION_PATH), "--serve"],
        input="\n".join(requests) + "\n",
        capture_output=True,
        text=True,
        timeout=30,
        check=True,
    )
    lines = completed.stdout.splitlines()
    assert lines
    for line in lines:
        json.loads(line)


def test_a_reply_with_the_wrong_id_is_refused():
    """An unmatched reply is an error, never the answer to this request.

    Accepting whatever line arrives next returns a stale result as if it were
    correct, and a wrong answer is worse than a raised exception.
    """
    client = solution.MCPClient(timeout_s=5.0)
    client.start()
    try:
        stale = {"jsonrpc": "2.0", "id": 999, "result": {"tools": []}}
        client._lines.put(json.dumps(stale) + "\n")
        with pytest.raises(RuntimeError, match="does not match"):
            client.list_tools()
    finally:
        client.close()


def test_a_result_kind_the_client_cannot_read_is_refused():
    """An unrecognised resultType is invalid rather than assumed complete.

    A server can answer that it needs more input before finishing. A client
    that reads such a reply as a finished result invents data.
    """
    client = solution.MCPClient(timeout_s=5.0)
    client.start()
    try:
        reply = {
            "jsonrpc": "2.0",
            "id": 1,
            "result": {"resultType": "input_required", "tools": []},
        }
        client._lines.put(json.dumps(reply) + "\n")
        with pytest.raises(RuntimeError, match="resultType"):
            client.list_tools()
    finally:
        client.close()


def test_close_tolerates_a_server_that_already_exited():
    """Shutting down twice, or after a crash, is not an error."""
    client = solution.MCPClient(timeout_s=5.0)
    client.start()
    client._process.kill()
    client._process.wait()
    client.close()
    client.close()
    assert client._process is None


def test_a_dead_server_reports_its_exit_code():
    """Once the tool is another process, "it died" has to be a clear failure.

    A raw BrokenPipeError names the pipe rather than the problem, and a client
    that waits out the full timeout cannot be told apart from a slow tool.
    """
    client = solution.MCPClient(timeout_s=30.0)
    client.start()
    client._process.kill()
    client._process.wait()
    try:
        with pytest.raises((RuntimeError, TimeoutError)) as caught:
            client.list_tools()
        assert "server exited" in str(caught.value)
    finally:
        client.close()


def test_the_agent_uses_a_tool_it_never_named(monkeypatch):
    """Step 6: the tools reaching the model are the ones off the wire.

    The model is stubbed because the protocol is what is under test, not the
    model. What matters is that the definitions handed to it come from
    tools/list and that the tool_result content came back from the server.
    """
    calls: list[list[dict]] = []

    def fake_complete_with_tools(messages, tools, **kwargs):
        calls.append(tools)
        if len(calls) == 1:
            return SimpleNamespace(
                stop_reason="tool_use",
                content=[_tool_use_block("tu_1", "get_stock_level", {"sku": "SKU-300"})],
            )
        return SimpleNamespace(
            stop_reason="end_turn",
            content=[_text_block("There are 47 units.")],
        )

    monkeypatch.setattr(solution, "complete_with_tools", fake_complete_with_tools)

    client = solution.MCPClient(timeout_s=10.0)
    client.start()
    try:
        discovered = client.list_tools()
        answer = solution.answer_with_discovered_tools("How many SKU-300?", client)
    finally:
        client.close()

    assert answer == "There are 47 units."
    # The definitions were not built in the agent; they are the server's,
    # translated into the shape the model API accepts.
    assert calls and calls[0] == solution.to_messages_api_tools(discovered)
    assert {tool["name"] for tool in calls[0]} == {
        "get_stock_level",
        "get_shipping_days",
    }


def test_the_agent_feeds_the_servers_result_back_to_the_model(monkeypatch):
    """The tool_result the model sees is what the server actually returned."""
    seen: list[list[dict]] = []

    def fake_complete_with_tools(messages, tools, **kwargs):
        seen.append(messages)
        if len(seen) == 1:
            return SimpleNamespace(
                stop_reason="tool_use",
                content=[_tool_use_block("tu_1", "get_stock_level", {"sku": "SKU-300"})],
            )
        return SimpleNamespace(stop_reason="end_turn", content=[_text_block("done")])

    monkeypatch.setattr(solution, "complete_with_tools", fake_complete_with_tools)

    client = solution.MCPClient(timeout_s=10.0)
    client.start()
    try:
        solution.answer_with_discovered_tools("How many SKU-300?", client)
    finally:
        client.close()

    results = [
        block
        for message in seen[-1]
        if isinstance(message.get("content"), list)
        for block in message["content"]
        if isinstance(block, dict) and block.get("type") == "tool_result"
    ]
    assert len(results) == 1
    assert results[0]["tool_use_id"] == "tu_1"
    # MCP said isError; the Messages API wants is_error. Another translation.
    assert results[0]["is_error"] is False
    # 47 is the server's inventory, not a number this test handed to the model.
    assert "47" in results[0]["content"]
