# Lab 10 - An MCP-style server

## Goal

After this lab you can build a minimal MCP server that exposes two tools over stdio using only the standard library, drive it from a client that discovers those tools at runtime, and explain why a protocol boundary between an agent and its tools is worth its overhead.

## Prerequisites

Labs 00, 01, and 07. Concepts: JSON-RPC request and response shape, `subprocess`, and line-delimited stdio.

## Estimated time

60 to 90 minutes

## Background

Every tool so far has been a Python function in the same process as the agent. That is the simplest thing that works, and it quietly couples four things together: the agent, the tool implementation, the tool's dependencies, and the tool's privileges.

A protocol boundary separates them. The tool runs as its own process, speaks a documented message format over stdio, and can be written in any language, deployed independently, and given a narrower set of permissions than the agent has. The same server then serves any client that speaks the protocol, instead of one agent's codebase.

This lab follows the shapes and rules of the `2026-07-28` MCP specification, using only the standard library rather than an SDK, so that the wire format is visible instead of hidden behind a client object. It implements the core of the protocol and leaves out the rest; the omissions are listed at the end so you know what you have and have not seen.

The message shape is JSON-RPC: one JSON object per line, each request carrying an id, a method, and params, and each response echoing the id with either a result or an error. Line-delimited JSON over stdio needs no HTTP server, no port, and no network permission, which is exactly why it is a good default for a local tool server.

The protocol is **stateless**, and this is the design decision worth understanding. There is no handshake. Earlier versions opened every connection with an `initialize` call that settled the protocol version and capabilities once, after which both sides assumed them; that method is gone. Instead every request carries its own protocol version and capabilities in a `_meta` block, which means a request is self-contained: any request can land on any server instance, and a server holds nothing about who is calling it. `server/discover` exists to ask a server which versions it speaks, but it is optional — a client that already knows can go straight to `tools/list`. The cost of dropping the handshake is that version checking now happens on every single call, which is why the server validates `_meta` before it looks at the method at all.

Discovery is the part that makes the boundary pay for itself. The client asks the server what tools it has and gets back names, descriptions, and schemas at runtime, instead of importing them at build time. Adding a tool to the server makes it available to every client without redeploying any of them. Because the catalogue is fetched rather than compiled in, the server also says how long it stays valid: `tools/list` returns a `ttlMs` and a `cacheScope` so a client can reuse it instead of choosing between refetching every turn and guessing. That only works if the server returns its tools in a deterministic order, which is also what keeps the model's prompt cache warm, since those definitions go into the context window verbatim.

The boundary also needs a translator, and this is the detail that catches people. MCP tool definitions and Messages API tool definitions look interchangeable and are not: MCP says `inputSchema` where the model API says `input_schema`, and MCP carries fields such as `title` and `annotations` that the model API will reject. Tool results have the same problem, with MCP returning a list of content blocks and an `isError` flag where the model API wants text and `is_error`. Forwarding either one untouched is a bug, so every real client has an adapter, and writing that adapter is the point: a protocol is a contract between two systems that were designed separately, not a shared data structure.

Error handling is part of the protocol too, and it has two layers that are easy to collapse into one. An unknown method, or a request missing its required metadata, is a JSON-RPC error object with a defined code, because that is a bug in the calling code and no amount of retrying will fix it. A tool that runs and fails is the opposite: it returns a normal result marked `isError`, because that is usually the model's mistake and the model can read the message and try again. Collapse the two and the model loses the only failure it could have recovered from.

Three more failures belong to the boundary itself rather than to either program. Stdout carries protocol messages and nothing else, so a single stray `print` in the server leaves the server working while the client dies decoding a greeting; diagnostics go to stderr. The reply id is not decoration: a client that returns whatever line arrives next will hand a caller a stale reply as if it were the answer, and a wrong result is far more expensive than a raised error. And a result now announces its own kind through `resultType`, because a server may answer that it needs more input before it can finish; a client that reads such a reply as a finished result invents data, so an unrecognised kind has to be refused rather than assumed.

## Steps

1. Implement `list_tools`: return the two tool definitions in MCP shape, with `inputSchema` rather than `input_schema`, in a deterministic order so the list can be cached.
2. Implement `call_tool`: dispatch by name, validate the arguments against the schema, and return a list of content blocks plus an `isError` flag, marking a failed call as an error result rather than raising.
3. Implement `check_request_meta`: reject a request that omits `protocolVersion` or `clientCapabilities` with code -32602, and one asking for a version you do not speak with code -32022, naming the versions you do support so the client can retry.
4. Implement `handle_request`: validate the metadata first, then route `server/discover`, `tools/list`, and `tools/call` by method, echo the request id, tag every result with `resultType` and `serverInfo`, attach the cache hints to `tools/list`, and return code -32601 for an unknown method. There is no `initialize`.
5. Implement `serve`: read line-delimited JSON from stdin, write one JSON response per line to stdout, and keep stdout free of anything that is not a protocol message.
6. Implement `MCPClient`: start the server with `subprocess`, attach the protocol metadata to every request, check that each reply id matches the request it answers, refuse a `resultType` you cannot read, cache the tool list for the `ttlMs` the server advertised, report a dead server by its exit code instead of a raw pipe error, and shut down cleanly even when the server has already exited.
7. Implement `to_messages_api_tools` and `answer_with_discovered_tools`: translate the discovered definitions into the shape the model API accepts, then execute each `tool_use` block with `tools/call` and translate the result back, without naming a single tool in the function. Steps 1 to 6 only show that the pipe works; this is the step that shows the pipe is worth having, so do not stop before it.

## Verification

```bash
pytest labs/track-2-tools-context/10-mcp-server/tests -v
```

The protocol is tested end to end offline, including a real subprocess round trip, because none of it needs a model. Step 7 is tested offline too, with the model stubbed: what is under test is that the definitions handed to it came off the wire and were translated, and that the `tool_result` fed back is what the server actually returned, neither of which needs a real completion.

Passing means discovery returns both tools with valid schemas in a stable order, a `tools/call` works as the very first request with no handshake while `initialize` is now just an unknown method, a request missing its protocol metadata is refused with -32602 and one naming an unsupported version with -32022 plus the alternatives, every result identifies its kind and its server, the tool list carries a cache hint that the client actually honours, a failing tool comes back as an error result naming the valid input, MCP definitions are translated rather than forwarded, an unknown method returns -32601 rather than crashing, a malformed line does not kill the server, every line the server writes to stdout parses as JSON, a reply whose id does not match is refused rather than returned, an unreadable `resultType` is refused rather than assumed complete, a dead server is reported by its exit code, and the client shuts the process down cleanly even when the process is already gone.

Running `main` needs a key only for the last section, and prints a clear skip message without one, so the protocol half of the lab stays runnable offline.

## Going further

- Run the server from a directory the agent process cannot read, and confirm the tool still works. That is the isolation argument made concrete.
- Add a third tool to the server without touching the client, and watch it appear through discovery.
- Delete the `resultType` check in the client and feed it an `input_required` reply. The client will report zero tools rather than an error, which is what "guessing at a result shape invents data" looks like in practice.
- The specification says a client should restart a server that exits unexpectedly, and that in-flight requests can simply be retried against the fresh process because there is no session to rebuild. Implement that, and notice it is the statelessness that makes a one-line retry correct.
- What this lab leaves out, so you know the edges of what you have built: pagination through `nextCursor` on long tool lists, `outputSchema` and `structuredContent` for machine-readable results, `notifications/cancelled` for abandoning a call in flight, `subscriptions/listen` for a server that pushes updates when its tool list changes, multi round-trip requests for a tool that needs to ask the user something mid-call, and the Streamable HTTP transport, which carries the same `_meta` fields as HTTP headers instead.

## Certification mapping

- **Anthropic, Building Effective Agents and Effective context engineering for AI agents**: Agent-computer interface design across a protocol boundary; tool discovery at runtime.
- **Databricks Generative AI Engineer Associate**: Tool and agent frameworks including MCP servers.
- **NVIDIA NCA Generative AI LLMs**: Software development; LLM integration and deployment.

Exam objectives change over time. Treat this as a pointer, not a syllabus, and check the official exam guides directly. See `docs/cert-mapping.md` for the full table.
