"""Thin MCP-style stdio server exposing lookup_order (lab 10 shape).

Purpose
    Speak a minimal JSON-RPC tools/list and tools/call protocol over stdin /
    stdout for a single read-only order lookup backed by the seeded SQLite DB.

Why
    Packaging layer demonstrates an MCP adapter without pulling the full agent
    loop into the transport. External clients can fetch account state through a
    familiar tool surface while policy still lives in the main desk process.

Trade-offs
    Only ``lookup_order`` is exposed—no refund/cancel (those need HITL in the
    main app). Protocol is a teaching subset, not a full MCP SDK. Each process
    start gets a fresh temp DB from seed.sql.

Edges
    Unknown tool/method → JSON-RPC error ``-32601``. Unknown order → text error
    with ``isError: true``. Blank stdin lines are skipped.
"""

from __future__ import annotations

import json
import sys
import tempfile
from typing import Any

from support_desk.tools_gate.db import get_order, init_db

PROTOCOL_VERSION = "2026-07-28"
META = "io.modelcontextprotocol/"


def list_tools() -> list[dict[str, Any]]:
    """Return the MCP tool descriptors this server advertises.

    Purpose
        Describe ``lookup_order`` input schema for tools/list.

    Why
        Keeps the catalog in one place for handle_request.

    Trade-offs
        Static list—no dynamic registration.

    Edges
        Single tool only.
    """
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
    """Dispatch one JSON-RPC request against the account connection.

    Purpose
        Implement ``tools/list`` and ``tools/call`` for ``lookup_order``.

    Why
        Pure function over connection makes the stdio loop trivial and testable.

    Trade-offs
        No initialize/handshake beyond echoing protocol meta on list. No
        batching.

    Edges
        Missing id is passed through. Unknown methods/tools return error
        objects, not exceptions.
    """
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
    """Run the stdio JSON-RPC loop until stdin EOF.

    Purpose
        Seed a temp DB and answer newline-delimited JSON requests forever.

    Why
        MCP-style packaging demo: one process, one tool, no HTTP stack.

    Trade-offs
        ``json.loads`` failures are not caught—malformed lines crash the
        process (acceptable for a lab adapter).

    Edges
        Blank lines skipped. Responses flushed per line. Returns 0 on EOF.
    """
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
