# Lab 10 - An MCP-style server

## Goal

After this lab you can build a minimal MCP-style server that exposes two tools over stdio using only the standard library, drive it from a client loop, and explain why a protocol boundary between an agent and its tools is worth its overhead.

## Prerequisites

Labs 00, 01, and 07. Concepts: JSON-RPC request and response shape, `subprocess`, and line-delimited stdio.

## Estimated time

60 to 90 minutes

## Background

Every tool so far has been a Python function in the same process as the agent. That is the simplest thing that works, and it quietly couples four things together: the agent, the tool implementation, the tool's dependencies, and the tool's privileges.

A protocol boundary separates them. The tool runs as its own process, speaks a documented message format over stdio, and can be written in any language, deployed independently, and given a narrower set of permissions than the agent has. The same server then serves any client that speaks the protocol, instead of one agent's codebase.

The message shape is JSON-RPC: one JSON object per line, each request carrying an id, a method, and params, and each response echoing the id with either a result or an error. Line-delimited JSON over stdio needs no HTTP server, no port, and no network permission, which is exactly why it is a good default for a local tool server.

Discovery is the part that makes the boundary pay for itself. The client asks the server what tools it has and gets back names, descriptions, and schemas at runtime, instead of importing them at build time. Adding a tool to the server makes it available to every client without redeploying any of them.

The costs are real and worth naming: serialization, process lifecycle, and a harder debugging story, since a crash is now on the other side of a pipe. For a single tool used by a single agent, a plain function is the right call. The boundary earns its keep when tools are shared across agents, need isolation, or belong to a different team.

Error handling is part of the protocol, not an afterthought. An unknown method is a JSON-RPC error object with a defined code, not a stack trace on stderr, and a tool that fails returns a result marked as an error so the model can read it and recover.

## Steps

1. Implement `list_tools`: return the two tool definitions with names, descriptions, and input schemas, in the same shape the Messages API expects.
2. Implement `call_tool`: dispatch by name, validate the arguments against the schema, and return a result marked as an error when the call fails.
3. Implement `handle_request`: route a decoded JSON-RPC object by method, echo the request id, and return a proper error object with code -32601 for an unknown method.
4. Implement `serve`: read line-delimited JSON from stdin, write one JSON response per line to stdout, and keep stdout free of anything that is not a protocol message.
5. Implement `MCPClient`: start the server with `subprocess`, send requests, read responses, and shut it down cleanly even when the server has already exited.
6. Wire the discovered tools into the augmented call from lab 01, so the agent uses tools it was never compiled against.

## Verification

```bash
pytest labs/track-2-tools-context/10-mcp-server/tests -v
```

The protocol is tested end to end offline, including a real subprocess round trip, because none of it needs a model. Passing means discovery returns both tools with valid schemas, a call executes and returns a result, an unknown method returns error code -32601 rather than crashing, a malformed line does not kill the server, and the client shuts the process down cleanly.

## Going further

- Run the server from a directory the agent process cannot read, and confirm the tool still works. That is the isolation argument made concrete.
- Add a third tool to the server without touching the client, and watch it appear through discovery.
- Kill the server mid-call and make the client report a clear failure instead of hanging forever.

## Certification mapping

- **Anthropic, Building Effective Agents and Effective context engineering for AI agents**: Agent-computer interface design across a protocol boundary; tool discovery at runtime.
- **Databricks Generative AI Engineer Associate**: Tool and agent frameworks including MCP servers.
- **NVIDIA NCA Generative AI LLMs**: Software development; LLM integration and deployment.

Exam objectives change over time. Treat this as a pointer, not a syllabus, and check the official exam guides directly. See `docs/cert-mapping.md` for the full table.
