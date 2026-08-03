"""Lab 10 - An MCP-style server (reference solution).

Two tools exposed over line-delimited JSON-RPC on stdio, using only the
standard library, plus a client that starts the server as a subprocess and
discovers the tools at runtime instead of importing them at build time.
"""

from __future__ import annotations

import json
import queue
import subprocess
import sys
import threading
from pathlib import Path
from typing import Any

INVENTORY: dict[str, int] = {
    "SKU-100": 12,
    "SKU-200": 0,
    "SKU-300": 47,
}

SHIPPING_DAYS: dict[str, str] = {
    "standard": "3 to 5 business days",
    "express": "the next business day for orders placed before 2pm",
}


def list_tools() -> list[dict[str, Any]]:
    """Return the tool definitions this server exposes."""
    # The definitions use the same shape the Messages API expects, so a
    # client can pass them straight through to the model unchanged.
    return [
        {
            "name": "get_stock_level",
            "description": (
                "Look up the current number of units in stock for one SKU. "
                "Call this whenever the user asks whether something is "
                "available, in stock, or how many are left."
            ),
            "input_schema": {
                "type": "object",
                "properties": {
                    "sku": {
                        "type": "string",
                        "description": "The SKU identifier to look up.",
                        "enum": sorted(INVENTORY),
                    }
                },
                "required": ["sku"],
            },
        },
        {
            "name": "get_shipping_days",
            "description": (
                "Look up how long a shipping method takes. Call this "
                "whenever the user asks when an order will arrive or how "
                "fast a shipping option is."
            ),
            "input_schema": {
                "type": "object",
                "properties": {
                    "method": {
                        "type": "string",
                        "description": "The shipping method to look up.",
                        "enum": sorted(SHIPPING_DAYS),
                    }
                },
                "required": ["method"],
            },
        },
    ]


def call_tool(name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    """Execute one tool and return its result."""
    # A failed tool call is a result the model can read and recover from,
    # never an exception thrown across the wire.
    tools = {tool["name"]: tool for tool in list_tools()}
    if name not in tools:
        known = ", ".join(sorted(tools))
        return {
            "content": f"Error: unknown tool {name!r}. Known tools are: {known}.",
            "is_error": True,
        }

    schema = tools[name]["input_schema"]
    for field in schema.get("required", []):
        if field not in arguments:
            return {
                "content": f"Error: missing required field {field!r}.",
                "is_error": True,
            }
    for field, spec in schema.get("properties", {}).items():
        allowed = spec.get("enum")
        if allowed and field in arguments and arguments[field] not in allowed:
            options = ", ".join(allowed)
            return {
                "content": (
                    f"Error: invalid value {arguments[field]!r} for {field!r}. "
                    f"Valid values are: {options}."
                ),
                "is_error": True,
            }

    if name == "get_stock_level":
        sku = arguments["sku"]
        return {"content": f"{sku} has {INVENTORY[sku]} units in stock.", "is_error": False}
    method = arguments["method"]
    return {"content": f"{method} shipping takes {SHIPPING_DAYS[method]}.", "is_error": False}


def handle_request(request: dict[str, Any]) -> dict[str, Any]:
    """Route one decoded JSON-RPC request and build the response."""
    # The id is echoed back so the client can match replies to calls even if
    # it ever pipelines more than one request.
    request_id = request.get("id")
    method = request.get("method")
    params = request.get("params") or {}

    if method == "initialize":
        result: dict[str, Any] = {
            "serverInfo": {"name": "lab-10-server", "version": "0.1"},
            "capabilities": {"tools": {}},
        }
    elif method == "tools/list":
        result = {"tools": list_tools()}
    elif method == "tools/call":
        result = call_tool(str(params.get("name", "")), params.get("arguments") or {})
    else:
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "error": {"code": -32601, "message": f"Method not found: {method!r}"},
        }
    return {"jsonrpc": "2.0", "id": request_id, "result": result}


def serve(stdin: Any, stdout: Any) -> None:
    """Read line-delimited JSON requests and write line-delimited responses."""
    for line in stdin:
        line = line.strip()
        if not line:
            continue
        try:
            request = json.loads(line)
        except json.JSONDecodeError:
            # A malformed line answers with a parse error and the loop keeps
            # reading; one bad client message must not kill the server.
            response = {
                "jsonrpc": "2.0",
                "id": None,
                "error": {"code": -32700, "message": "Parse error: invalid JSON."},
            }
        else:
            response = handle_request(request)
        # stdout carries protocol messages only. Anything else, including a
        # stray print, corrupts the stream; diagnostics belong on stderr.
        stdout.write(json.dumps(response) + "\n")
        stdout.flush()


class MCPClient:
    """Start the server as a subprocess and talk to it."""

    def __init__(self, timeout_s: float = 10.0) -> None:
        self._timeout_s = timeout_s
        self._process: subprocess.Popen[str] | None = None
        self._lines: queue.Queue[str] = queue.Queue()
        self._next_id = 0

    def start(self) -> None:
        """Launch the server process and begin reading its responses."""
        self._process = subprocess.Popen(
            [sys.executable, str(Path(__file__).resolve()), "--serve"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            text=True,
        )
        # A daemon thread drains stdout into a queue so that requests can
        # time out instead of blocking forever on a server that never answers.
        threading.Thread(target=self._drain_stdout, daemon=True).start()

    def _drain_stdout(self) -> None:
        process = self._process
        if process is None or process.stdout is None:
            return
        for line in process.stdout:
            self._lines.put(line)

    def _request(self, method: str, params: dict[str, Any] | None = None) -> Any:
        process = self._process
        if process is None or process.stdin is None:
            raise RuntimeError("client is not started; call start() first")
        self._next_id += 1
        request: dict[str, Any] = {"jsonrpc": "2.0", "id": self._next_id, "method": method}
        if params is not None:
            request["params"] = params
        process.stdin.write(json.dumps(request) + "\n")
        process.stdin.flush()
        try:
            line = self._lines.get(timeout=self._timeout_s)
        except queue.Empty as exc:
            raise TimeoutError(
                f"no response to {method!r} within {self._timeout_s}s"
            ) from exc
        response = json.loads(line)
        if "error" in response:
            error = response["error"]
            raise RuntimeError(f"{method!r} failed: {error['message']} ({error['code']})")
        return response["result"]

    def list_tools(self) -> list[dict[str, Any]]:
        """Discover the server's tools at runtime."""
        return self._request("tools/list")["tools"]

    def call(self, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        """Invoke one tool on the server."""
        return self._request("tools/call", {"name": name, "arguments": arguments})

    def close(self) -> None:
        """Shut the server down, tolerating a process that already exited."""
        process = self._process
        self._process = None
        if process is None:
            return
        try:
            if process.stdin is not None:
                # Closing stdin ends the server's read loop, which is the
                # clean shutdown path; kill is only the fallback.
                process.stdin.close()
            process.wait(timeout=2.0)
        except Exception:
            process.kill()
            try:
                process.wait(timeout=2.0)
            except Exception:
                pass


def main() -> int:
    """Run the lab end to end and print what happened."""
    # The same file is both programs: with --serve it is the server the
    # client launches, without it it is the demo driving that server.
    if "--serve" in sys.argv[1:]:
        serve(sys.stdin, sys.stdout)
        return 0

    client = MCPClient()
    client.start()
    try:
        tools = client.list_tools()
        print(f"discovered {len(tools)} tools:")
        for tool in tools:
            print(f"  {tool['name']}: {tool['description'][:56]}...")

        good = client.call("get_stock_level", {"sku": "SKU-200"})
        print(f"\ncall get_stock_level(SKU-200) -> {good['content']}")

        bad = client.call("get_stock_level", {"sku": "SKU-999"})
        print(f"call get_stock_level(SKU-999) -> {bad['content']}")
    finally:
        client.close()
    print("\nserver shut down cleanly")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
