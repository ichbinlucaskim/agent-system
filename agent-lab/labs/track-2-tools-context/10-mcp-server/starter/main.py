"""Lab 10 - An MCP-style server (starter).

Goal: Build a minimal MCP server that exposes two tools over stdio using only the standard library, drive it from a client that discovers those tools at runtime, and explain why a protocol boundary between an agent and its tools is worth its overhead.

Fill in each function below. Every one carries a TODO describing what to
do and which step of the README it maps to. Run the tests with:

    pytest labs/track-2-tools-context/10-mcp-server/tests -v
"""

from __future__ import annotations

from typing import Any

# TODO: step 3. The version this file speaks, and the versions it accepts from
# a client. There is no handshake, so every request states its version and the
# server checks it on every call.
PROTOCOL_VERSION = ""
SUPPORTED_VERSIONS: list[str] = []

# Reserved _meta keys are namespaced under this prefix.
META = "io.modelcontextprotocol/"

# TODO: step 4. Who this server says it is, in every result it returns.
SERVER_INFO: dict[str, Any] = {}
CLIENT_INFO: dict[str, Any] = {}

# TODO: step 4. How long a client may reuse the tool catalogue, in ms.
TOOL_LIST_TTL_MS = 0


def list_tools() -> list[dict[str, Any]]:
    """Return the tool definitions this server exposes, in MCP shape."""
    # TODO: step 1. Two tools, each with name, description, and inputSchema.
    # Note the spelling: MCP is camelCase and the Messages API is snake_case,
    # so these cannot be handed to the model unchanged. Return them in a
    # deterministic order, which is what makes the list cacheable by a client
    # and keeps the model's prompt cache warm.
    raise NotImplementedError


def text_content(text: str) -> list[dict[str, Any]]:
    """Wrap a string as the single text block of a tool result."""
    raise NotImplementedError


def text_of_content(content: list[dict[str, Any]]) -> str:
    """Join the text blocks of a tool result into one string."""
    raise NotImplementedError


def call_tool(name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    """Execute one tool and return its result."""
    # TODO: step 2. Dispatch by name, validate arguments against the schema,
    # and return {'content': [content blocks], 'isError': bool}. A failed tool
    # is a result, not an exception across the wire: the model can read an
    # error result and retry, and can do nothing with a protocol error.
    raise NotImplementedError


def check_request_meta(params: dict[str, Any]) -> dict[str, Any] | None:
    """Validate the per-request protocol fields, returning an error or None."""
    # TODO: step 3. A request missing protocolVersion or clientCapabilities is
    # -32602. A version you do not speak is -32022, and the error data should
    # name the versions you do support so the client can retry rather than
    # only learn that it failed. Skip this and you quietly serve a client that
    # may speak a different protocol, because no handshake checked it either.
    raise NotImplementedError


def handle_request(request: dict[str, Any]) -> dict[str, Any]:
    """Route one decoded JSON-RPC request and build the response."""
    # TODO: step 4. Validate the metadata first, then support 'server/discover',
    # 'tools/list', and 'tools/call'. There is no 'initialize'. Echo the
    # request id. Tag every result with resultType 'complete' and with
    # serverInfo, since no handshake announced either. Attach ttlMs and
    # cacheScope to 'tools/list'. An unknown method returns an error object
    # with code -32601, not a traceback.
    raise NotImplementedError


def serve(stdin: Any, stdout: Any) -> None:
    """Read line-delimited JSON requests and write line-delimited responses."""
    # TODO: step 5. One JSON object per line. Never write anything else to stdout: a stray print corrupts the stream. Log to stderr instead. A line that fails to parse returns a -32700 error and the loop continues.
    raise NotImplementedError


def to_messages_api_tools(mcp_tools: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Translate MCP tool definitions into Messages API tool definitions."""
    # TODO: step 7. inputSchema becomes input_schema, and MCP-only fields such
    # as title are dropped. The two shapes look interchangeable and are not,
    # which is why a protocol needs an adapter rather than a shared struct.
    raise NotImplementedError


class MCPClient:
    """Start the server as a subprocess and talk to it."""

    # TODO: step 6. Implement start, discover, list_tools, call, and close.
    # Attach the protocol metadata to every request, since nothing was agreed
    # up front. Check that the reply id matches the id you sent: taking
    # whatever line arrives next returns a stale result as if it were correct,
    # and a wrong answer costs more than a raised error. Refuse a resultType
    # you cannot read instead of assuming it finished. Cache the tool list for
    # the ttlMs the server advertised. Report a dead server by its exit code
    # rather than letting a BrokenPipeError through, which names the pipe
    # instead of the problem, and do not block forever on a call that never
    # answers. close must not raise when the server has already exited.


def answer_with_discovered_tools(question: str, client: MCPClient, *, max_tool_rounds: int = 3) -> str:
    """Answer a question using tools this code never named."""
    # TODO: step 7. Translate the definitions from tools/list, hand them to
    # the model, execute each tool_use block with tools/call, and translate
    # the result back for the tool_result block. Do not name a tool anywhere
    # in this function: if you do, you have rebuilt the compile-time coupling
    # the protocol boundary exists to remove. This is the step that shows the
    # boundary paying for itself, so do not stop at step 6.
    raise NotImplementedError


def main() -> int:
    """Run the lab end to end and print what happened."""
    # TODO: final step. Wire the functions above together and print
    # enough that the behaviour described in the README is visible. The same
    # file is both programs: with --serve it is the server the client
    # launches, without it it is the demo driving that server.
    raise NotImplementedError


if __name__ == "__main__":
    raise SystemExit(main())
