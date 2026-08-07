"""MCP order server tools/list and tools/call over one request."""

from __future__ import annotations

import tempfile

from support_desk.tools_gate.db import init_db
from support_desk.packaging.mcp_order_server import handle_request, list_tools


def test_list_tools_exposes_lookup_order():
    names = [t["name"] for t in list_tools()]
    assert names == ["lookup_order"]


def test_tools_call_lookup():
    tmp = tempfile.NamedTemporaryFile(suffix=".sqlite", delete=False)
    tmp.close()
    connection = init_db(tmp.name)
    response = handle_request(
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": "lookup_order",
                "arguments": {"order_id": "ORD-100"},
            },
        },
        connection,
    )
    assert response["id"] == 1
    text = response["result"]["content"][0]["text"]
    assert "ORD-100" in text
    assert response["result"]["isError"] is False
