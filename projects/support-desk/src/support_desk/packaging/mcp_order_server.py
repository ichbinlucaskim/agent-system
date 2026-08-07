"""Thin MCP-style stdio server exposing lookup_order (lab 10 shape)."""

from __future__ import annotations

import json
import sys
import tempfile
from typing import Any

from support_desk.tools_gate.db import get_order, init_db

PROTOCOL_VERSION = "2026-07-28"
META = "io.modelcontextprotocol/"


def list_tools() -> list[dict[str, Any]]:
    return [
        {
            "name": "lookup_order",
            "title": "Order lookup",
            "description": (
                "Fetch one order from the account database by id. "
                "Call before refund or cancel decisions."
            ),
            "inputSchema": {
                "type": "object",
                "properties": {
                    "order_id": {
                        "type": "string",
                        "description": "Order id such as ORD-100.",
                    }
                },
                "required": ["order_id"],
            },
        }
    ]


def handle_request(message: dict[str, Any], connection) -> dict[str, Any]:
    req_id = message.get("id")
    method = message.get("method")
    params = message.get("params") or {}

    if method == "tools/list":
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "tools": list_tools(),
                "_meta": {f"{META}protocolVersion": PROTOCOL_VERSION},
            },
        }

    if method == "tools/call":
        name = params.get("name")
        arguments = params.get("arguments") or {}
        if name != "lookup_order":
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "error": {"code": -32601, "message": f"unknown tool {name!r}"},
            }
        order_id = str(arguments.get("order_id", "")).strip().upper()
        order = get_order(connection, order_id)
        text = (
            json.dumps(order, sort_keys=True)
            if order
            else f"Error: unknown order {order_id!r}."
        )
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "content": [{"type": "text", "text": text}],
                "isError": order is None,
            },
        }

    return {
        "jsonrpc": "2.0",
        "id": req_id,
        "error": {"code": -32601, "message": f"unknown method {method!r}"},
    }


def main() -> int:
    tmp = tempfile.NamedTemporaryFile(suffix=".sqlite", delete=False)
    tmp.close()
    connection = init_db(tmp.name)
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        message = json.loads(line)
        response = handle_request(message, connection)
        sys.stdout.write(json.dumps(response) + "\n")
        sys.stdout.flush()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
