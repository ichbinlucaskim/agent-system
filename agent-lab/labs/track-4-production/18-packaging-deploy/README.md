# Lab 18 - Packaging and deployment

## Goal

After this lab you can wrap an agent as both a CLI and a thin HTTP handler using only the standard library, drive its configuration entirely through the environment, and prove it starts and answers with a smoke test.

## Prerequisites

Labs 12, 15, 16, and 17. Concepts: environment configuration, `argparse`, and `http.server`.

## Estimated time

45 to 60 minutes

## Background

This lab is marked optional because it teaches packaging rather than agent design. It is where an agent stops being a script that works on your machine, and most of the work turns out to be about configuration and failure rather than about the model.

Two entry points, one core. The CLI and the HTTP handler should both be thin adapters over the same function. When they are not, they drift, and the bug you fix in one comes back through the other a month later.

Configuration comes from the environment, and it is validated at startup rather than at first use. A process that starts happily and fails on its first request an hour later is much harder to diagnose than one that refuses to start and says which variable is missing.

The HTTP handler here is `http.server`, which is not a production server and should not pretend to be one. It exists to show the shape: parse a request, call the core, serialize a response, return a status code that means something. Swapping in a real server later changes the adapter, not the agent.

Health checks must not depend on the model. A `/health` endpoint that makes an API call costs money on every probe and reports the provider's availability rather than yours. Report that the process is up and correctly configured, and leave upstream checks to a separate deeper probe.

A smoke test is the minimum honest deployment check: does the thing start, does it answer, does a malformed request produce a clean error rather than a stack trace. It is not an evaluation of quality, which is lab 15, and confusing the two leaves you with a green pipeline and an agent that answers everything wrongly.

## Steps

1. Define `Config` and `load_config`: read every setting from the environment, apply defaults, and raise a clear error naming any required variable that is missing.
2. Implement `answer`: the single core function both entry points call, taking a question and returning a structured result.
3. Implement `build_parser` and `run_cli`: parse arguments, call `answer`, print the result, and return a non-zero exit code on failure so a shell can branch on it.
4. Implement `AgentHandler`: a `BaseHTTPRequestHandler` with a `/health` endpoint that touches no model and a POST endpoint that returns 400 on malformed input and 200 with a JSON body otherwise.
5. Implement `smoke_test`: start the server, hit `/health`, post one malformed request and one valid one, and report a single pass or fail.
6. Document the required environment variables in the module docstring, and confirm the process refuses to start without them.

## Verification

```bash
pytest labs/track-4-production/18-packaging-deploy/tests -v
```

Configuration, argument parsing, and HTTP status handling are tested offline. Passing means a missing required variable is reported by name at startup, `/health` returns 200 with no API key set, malformed JSON returns 400 rather than a traceback, the CLI returns a non-zero exit code on failure, and both entry points call the same core function.

## Going further

- Add a request id to every response and thread it through the trace from lab 16, so one log line leads to one full run.
- Add a concurrency limit to the handler and decide what a rejected request should receive: a 429, a queue, or a wait.
- Run the smoke test against a deliberately misconfigured environment and confirm the failure message says which variable was wrong.

## Certification mapping

- **Anthropic, Building Effective Agents and Effective context engineering for AI agents**: Taking an agent to production: one core behind thin entry points.
- **Databricks Generative AI Engineer Associate**: Assembling and deploying applications; governance.
- **NVIDIA NCA Generative AI LLMs**: LLM integration and deployment; software development.

Exam objectives change over time. Treat this as a pointer, not a syllabus, and check the official exam guides directly. See `docs/cert-mapping.md` for the full table.
