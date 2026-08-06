"""Lab 10 - An MCP-style server (reference solution).

Two tools exposed over line-delimited JSON-RPC on stdio, following the shape of
the 2026-07-28 MCP specification, using only the standard library. Plus a
client that launches the server as a subprocess, discovers the tools at
runtime, and an agent call that uses those tools without naming any of them.

The protocol is stateless: there is no handshake, and every request carries its
own protocol version and capabilities in `_meta`. That is what lets any request
land on any server instance, and it is why this lab has no `initialize` call.
"""

from __future__ import annotations

import json
import queue
import subprocess
import sys
import threading
import time
from pathlib import Path
from typing import Any

from common.client import MissingAPIKeyError, complete_with_tools, text_of, tool_uses

# The version this file speaks. Clients send it on every request and servers
# answer with the versions they support, so mismatches surface on the first
# call instead of being negotiated once and then assumed forever.
PROTOCOL_VERSION = "2026-07-28"
SUPPORTED_VERSIONS: list[str] = [PROTOCOL_VERSION]

# Reserved `_meta` keys are namespaced. Anything a lab or vendor invents lives
# under its own reverse-DNS prefix instead.
META = "io.modelcontextprotocol/"

SERVER_INFO: dict[str, Any] = {"name": "lab-10-server", "version": "0.1"}
CLIENT_INFO: dict[str, Any] = {"name": "lab-10-client", "version": "0.1"}

# How long a client may reuse a tool catalogue. Advertising this is what makes
# caching safe: without it a client either refetches every turn or guesses.
TOOL_LIST_TTL_MS = 300_000

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
    """Return the tool definitions this server exposes, in MCP shape."""
    # Note inputSchema, not input_schema. MCP is camelCase and the Anthropic
    # Messages API is snake_case, so a client has to translate rather than
    # forward these unchanged; see to_messages_api_tools.
    tools = [
        {
            "name": "get_stock_level",
            "title": "Stock level lookup",
            "description": (
                "Look up the current number of units in stock for one SKU. "
                "Call this whenever the user asks whether something is "
                "available, in stock, or how many are left."
            ),
            "inputSchema": {
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
            "title": "Shipping duration lookup",
            "description": (
                "Look up how long a shipping method takes. Call this "
                "whenever the user asks when an order will arrive or how "
                "fast a shipping option is."
            ),
            "inputSchema": {
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
    # Deterministic order is what lets a client cache this list and keeps the
    # model's prompt cache stable, since the tools go into the window verbatim.
    return sorted(tools, key=lambda tool: tool["name"])


def text_content(text: str) -> list[dict[str, Any]]:
    """Wrap a string as the single text block of a tool result."""
    return [{"type": "text", "text": text}]


def text_of_content(content: list[dict[str, Any]]) -> str:
    """Join the text blocks of a tool result into one string."""
    return "".join(block["text"] for block in content if block.get("type") == "text")


def call_tool(name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    """Execute one tool and return its result."""
    # A tool that runs and fails is a result with isError set, never an
    # exception thrown across the wire. Clients pass these to the model
    # precisely because the model can read them and retry; a protocol error
    # would give it nothing to act on.
    tools = {tool["name"]: tool for tool in list_tools()}
    if name not in tools:
        known = ", ".join(sorted(tools))
        return {
            "content": text_content(
                f"Error: unknown tool {name!r}. Known tools are: {known}."
            ),
            "isError": True,
        }

    schema = tools[name]["inputSchema"]
    for field in schema.get("required", []):
        if field not in arguments:
            return {
                "content": text_content(f"Error: missing required field {field!r}."),
                "isError": True,
            }
    for field, spec in schema.get("properties", {}).items():
        allowed = spec.get("enum")
        if allowed and field in arguments and arguments[field] not in allowed:
            options = ", ".join(allowed)
            return {
                "content": text_content(
                    f"Error: invalid value {arguments[field]!r} for {field!r}. "
                    f"Valid values are: {options}."
                ),
                "isError": True,
            }

    if name == "get_stock_level":
        sku = arguments["sku"]
        return {
            "content": text_content(f"{sku} has {INVENTORY[sku]} units in stock."),
            "isError": False,
        }
    method = arguments["method"]
    return {
        "content": text_content(f"{method} shipping takes {SHIPPING_DAYS[method]}."),
        "isError": False,
    }


def _error(request_id: Any, code: int, message: str, data: Any = None) -> dict[str, Any]:
    """Build a JSON-RPC error response."""
    error: dict[str, Any] = {"code": code, "message": message}
    if data is not None:
        error["data"] = data
    return {"jsonrpc": "2.0", "id": request_id, "error": error}


def check_request_meta(params: dict[str, Any]) -> dict[str, Any] | None:
    """Validate the per-request protocol fields, returning an error or None.

    Replacing the handshake with per-request metadata moves version checking
    into every call. The payoff is that the server holds no connection state,
    so requests can be load balanced across instances; the price is this
    validation, and skipping it means silently serving a client that speaks a
    version you do not.
    """
    meta = params.get("_meta") or {}
    for field in ("protocolVersion", "clientCapabilities"):
        if f"{META}{field}" not in meta:
            return {
                "code": -32602,
                "message": f"Invalid params: missing _meta {META}{field}",
            }
    version = meta[f"{META}protocolVersion"]
    if version not in SUPPORTED_VERSIONS:
        return {
            "code": -32022,
            "message": f"Unsupported protocol version: {version!r}",
            "data": {"supported": SUPPORTED_VERSIONS},
        }
    return None


def handle_request(request: dict[str, Any]) -> dict[str, Any]:
    """Route one decoded JSON-RPC request and build the response."""
    # The id is echoed back because it is what makes a reply belong to a call.
    # The client checks it; see MCPClient._request for why accepting an
    # unmatched reply is a wrong answer rather than an error.
    request_id = request.get("id")
    method = request.get("method")
    params = request.get("params") or {}

    problem = check_request_meta(params)
    if problem is not None:
        return _error(request_id, problem["code"], problem["message"], problem.get("data"))

    if method == "server/discover":
        # The modern replacement for the initialize handshake. It is optional:
        # a client that already knows the version can go straight to
        # tools/list. Its other job is probing a server of unknown vintage.
        result: dict[str, Any] = {
            "resultType": "complete",
            "supportedVersions": SUPPORTED_VERSIONS,
            "capabilities": {"tools": {"listChanged": False}},
        }
    elif method == "tools/list":
        result = {
            "resultType": "complete",
            "tools": list_tools(),
            "ttlMs": TOOL_LIST_TTL_MS,
            "cacheScope": "public",
        }
    elif method == "tools/call":
        result = {
            "resultType": "complete",
            **call_tool(str(params.get("name", "")), params.get("arguments") or {}),
        }
    else:
        return _error(request_id, -32601, f"Method not found: {method!r}")

    # Every result carries resultType so a client can tell a finished call from
    # one that needs more input, and serverInfo so it knows who answered
    # without having done a handshake.
    result.setdefault("_meta", {})[f"{META}serverInfo"] = SERVER_INFO
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
            response = _error(None, -32700, "Parse error: invalid JSON.")
        else:
            response = handle_request(request)
        # stdout carries protocol messages only. Anything else, including a
        # stray print, corrupts the stream; diagnostics belong on stderr.
        stdout.write(json.dumps(response) + "\n")
        stdout.flush()


def to_messages_api_tools(mcp_tools: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Translate MCP tool definitions into Messages API tool definitions.

    The two shapes are close enough to look interchangeable and are not: MCP
    says inputSchema, the Messages API says input_schema, and MCP carries
    fields such as title and annotations that the model API does not accept.
    Every real client has an adapter like this, and forwarding the definitions
    untouched is the mistake it exists to prevent.
    """
    return [
        {
            "name": tool["name"],
            "description": tool["description"],
            "input_schema": tool["inputSchema"],
        }
        for tool in mcp_tools
    ]


class MCPClient:
    """Start the server as a subprocess and talk to it."""

    def __init__(self, timeout_s: float = 10.0) -> None:
        self._timeout_s = timeout_s
        self._process: subprocess.Popen[str] | None = None
        self._lines: queue.Queue[str] = queue.Queue()
        self._next_id = 0
        self._tool_cache: list[dict[str, Any]] | None = None
        self._tool_cache_expires_at = 0.0

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
        request_id = self._next_id
        # Protocol fields ride along on every request rather than being agreed
        # once, which is what makes the server free of connection state.
        body: dict[str, Any] = dict(params or {})
        body["_meta"] = {
            f"{META}protocolVersion": PROTOCOL_VERSION,
            f"{META}clientInfo": CLIENT_INFO,
            f"{META}clientCapabilities": {},
        }
        request = {"jsonrpc": "2.0", "id": request_id, "method": method, "params": body}
        try:
            process.stdin.write(json.dumps(request) + "\n")
            process.stdin.flush()
        except (BrokenPipeError, ValueError) as exc:
            # Once the tool lives in another process, "the tool died" is a
            # normal failure. Report the exit code instead of letting a raw
            # pipe error surface, which says nothing about what happened.
            raise RuntimeError(
                f"server exited with code {process.poll()} before "
                f"{method!r} could be sent"
            ) from exc
        line = self._read_reply(process, method)
        response = json.loads(line)
        # The id is what makes a reply belong to a call. Skip this check and a
        # stale or duplicated line is accepted as the answer to the current
        # request, which is a wrong result rather than an error, and wrong
        # results are the expensive kind. A client that pipelined requests
        # would keep a table of pending ids rather than refusing here.
        if response.get("id") != request_id:
            raise RuntimeError(
                f"reply id {response.get('id')!r} does not match "
                f"request id {request_id!r} for {method!r}"
            )
        if "error" in response:
            error = response["error"]
            raise RuntimeError(f"{method!r} failed: {error['message']} ({error['code']})")
        result = response["result"]
        # An absent resultType means an older server and is read as complete.
        # Anything this client does not recognise is invalid rather than
        # assumed, because guessing at a result shape invents data.
        result_type = result.get("resultType", "complete")
        if result_type != "complete":
            raise RuntimeError(f"{method!r} returned unsupported resultType {result_type!r}")
        return result

    def _read_reply(self, process: subprocess.Popen[str], method: str) -> str:
        """Wait for one reply line, giving up early if the server is gone."""
        # Polling in small slices rather than blocking for the whole timeout
        # turns "the server crashed" into an immediate, named failure instead
        # of a wait that looks identical to a slow tool.
        deadline = time.monotonic() + self._timeout_s
        while True:
            try:
                return self._lines.get(timeout=0.05)
            except queue.Empty:
                pass
            exited = process.poll()
            if exited is not None:
                # The server may have written a reply just before exiting, so
                # look once more before calling it a crash.
                try:
                    return self._lines.get(timeout=0.2)
                except queue.Empty:
                    raise RuntimeError(
                        f"server exited with code {exited} without answering {method!r}"
                    ) from None
            if time.monotonic() >= deadline:
                raise TimeoutError(
                    f"no response to {method!r} within {self._timeout_s}s"
                )

    def discover(self) -> dict[str, Any]:
        """Ask the server which protocol versions it speaks."""
        return self._request("server/discover")

    def list_tools(self, *, refresh: bool = False) -> list[dict[str, Any]]:
        """Discover the server's tools at runtime, honouring the cache hint."""
        if not refresh and self._tool_cache is not None:
            if time.monotonic() < self._tool_cache_expires_at:
                return self._tool_cache
        result = self._request("tools/list")
        self._tool_cache = result["tools"]
        # The server says how long its catalogue stays valid, so the client
        # does not have to choose between refetching every turn and guessing.
        self._tool_cache_expires_at = time.monotonic() + result.get("ttlMs", 0) / 1000.0
        return self._tool_cache

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
                # clean shutdown path and the only portable one; kill is the
                # fallback for a server that ignores end-of-file.
                process.stdin.close()
            process.wait(timeout=2.0)
        except Exception:
            process.kill()
            try:
                process.wait(timeout=2.0)
            except Exception:
                pass


def answer_with_discovered_tools(
    question: str,
    client: MCPClient,
    *,
    max_tool_rounds: int = 3,
) -> str:
    """Answer a question using tools this code never named.

    Nothing here mentions get_stock_level or get_shipping_days. The
    definitions arrive over the wire, are translated into the shape the model
    API wants, and every tool_use block is executed by sending tools/call back
    down the same pipe. That is the payoff for the protocol boundary: adding a
    tool to the server is enough to make it usable here, with no change to the
    agent and no redeploy of it.
    """
    tools = to_messages_api_tools(client.list_tools())
    messages: list[dict[str, Any]] = [{"role": "user", "content": question}]

    response = None
    for _ in range(max_tool_rounds):
        response = complete_with_tools(messages, tools)
        messages.append({"role": "assistant", "content": response.content})
        if response.stop_reason != "tool_use":
            break
        # Every tool_use block needs exactly one tool_result, and all results
        # go back in a single user message.
        results: list[dict[str, Any]] = []
        for block in tool_uses(response):
            outcome = client.call(block.name, dict(block.input))
            results.append(
                {
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    # MCP returns content blocks and isError; the Messages API
                    # wants text and is_error. Another translation, same reason.
                    "content": text_of_content(outcome["content"]),
                    "is_error": outcome.get("isError", False),
                }
            )
        messages.append({"role": "user", "content": results})

    return text_of(response) if response is not None else ""


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
        discovered = client.discover()
        print(f"server speaks: {discovered['supportedVersions']}")
        print(f"  no handshake was needed; this call was optional")

        tools = client.list_tools()
        print(f"\ndiscovered {len(tools)} tools:")
        for tool in tools:
            print(f"  {tool['name']}: {tool['description'][:52]}...")

        good = client.call("get_stock_level", {"sku": "SKU-200"})
        print(f"\ncall get_stock_level(SKU-200) -> {text_of_content(good['content'])}")

        bad = client.call("get_stock_level", {"sku": "SKU-999"})
        print(f"call get_stock_level(SKU-999) -> {text_of_content(bad['content'])}")
        print(f"  isError {bad['isError']}, so the model can read it and retry")

        # Step 6. Everything above proves the pipe works. This proves the pipe
        # is worth having: the model picks a tool this file never names.
        question = "Is SKU-300 in stock, and how fast is express shipping?"
        print(f"\nasking the model: {question}")
        try:
            print(f"  {answer_with_discovered_tools(question, client)}")
        except MissingAPIKeyError as exc:
            print(f"  skipped, needs a model: {exc}")
    finally:
        client.close()
    print("\nserver shut down cleanly")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
