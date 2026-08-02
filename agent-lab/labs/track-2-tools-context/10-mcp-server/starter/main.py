"""Lab 10 - An MCP-style server (starter).

Goal: Build a minimal MCP-style server that exposes two tools over stdio using only the standard library, drive it from a client loop, and explain why a protocol boundary between an agent and its tools is worth its overhead.

Fill in each function below. Every one carries a TODO describing what to
do and which step of the README it maps to. Run the tests with:

    pytest labs/track-2-tools-context/10-mcp-server/tests -v
"""

from __future__ import annotations

from typing import Any


def list_tools() -> list[dict[str, Any]]:
    """Return the tool definitions this server exposes."""
    # TODO: step 1. Two tools, each with name, description, and input_schema, in the same shape the Messages API expects so the client can pass them through unchanged.
    raise NotImplementedError


def call_tool(name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    """Execute one tool and return its result."""
    # TODO: step 2. Dispatch by name, validate arguments against the schema, and return {'content': ..., 'is_error': bool}. A failed tool is a result, not an exception across the wire.
    raise NotImplementedError


def handle_request(request: dict[str, Any]) -> dict[str, Any]:
    """Route one decoded JSON-RPC request and build the response."""
    # TODO: step 3. Support 'initialize', 'tools/list', and 'tools/call'. Echo the request id. An unknown method returns an error object with code -32601, not a traceback.
    raise NotImplementedError


def serve(stdin: Any, stdout: Any) -> None:
    """Read line-delimited JSON requests and write line-delimited responses."""
    # TODO: step 4. One JSON object per line. Never write anything else to stdout: a stray print corrupts the stream. Log to stderr instead. A line that fails to parse returns a -32700 error and the loop continues.
    raise NotImplementedError


class MCPClient:
    """Start the server as a subprocess and talk to it."""

    # TODO: step 5. Implement start, list_tools, call, and close. close must not raise when the server has already exited, and a call must not block forever if it never answers.


def main() -> int:
    """Run the lab end to end and print what happened."""
    # TODO: final step. Wire the functions above together and print
    # enough that the behaviour described in the README is visible.
    raise NotImplementedError


if __name__ == "__main__":
    raise SystemExit(main())
