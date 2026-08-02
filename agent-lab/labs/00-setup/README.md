# Lab 00 - Setup

## Goal

After this lab you can authenticate against the Claude API from a local environment, send a Messages API request, choose deliberately between a streaming and a non-streaming response, and read the token usage that every response reports.

## Prerequisites

None beyond Python 3.11 or newer and an Anthropic API key. Concepts: environment variables, and the idea that a model call is a request and a response over HTTP.

## Estimated time

20 to 30 minutes

## Background

The API key is a secret. It lives in an environment variable, never in source code, never in a prompt, and never in a file that git tracks. This repository ships `.env.example` as a placeholder and git-ignores `.env`. `common/client.py` reads `ANTHROPIC_API_KEY` and raises a named error when it is absent, so a missing credential fails immediately instead of halfway through a run.

A Messages API request needs three things: a `model`, a `max_tokens` ceiling, and a `messages` list of role and content pairs. The response is not a string. Its `content` is a list of blocks, and a text block is not always the first one, so always filter blocks by type rather than indexing `content[0]`. The response also carries `stop_reason`, which tells you why generation ended, and `usage`.

Streaming and non-streaming produce the same answer. What differs is when the caller sees it. A non-streaming call blocks until the entire response has been generated, which is fine for a short classification and a problem for a long one, since a large `max_tokens` on a non-streaming request risks an HTTP timeout. A streaming call yields text deltas as they are produced, so a person watching a screen sees progress immediately.

`max_tokens` is a hard ceiling on everything the model emits, including its thinking. On models where thinking is on by default, a limit sized only for the visible answer can truncate the response mid-sentence. When you see `stop_reason` come back as `max_tokens`, that is what happened.

Token usage is the unit of both cost and context budget, and everything later in this course is measured in it. Note that `input_tokens` counts only the uncached remainder of the prompt: the full prompt size is input tokens plus cache reads plus cache writes. A run that looks cheap because `input_tokens` is small may simply be reading a large cache.

## Steps

1. Implement `mask` so an API key can be printed without leaking it. Keep a short prefix and suffix, replace the middle, and return only dots for a key too short to have a safe prefix.
2. Implement `check_api_key`. Call `read_api_key` from `common.client` and return the masked form. Let `MissingAPIKeyError` propagate: a missing credential should stop the run, not degrade it.
3. Implement `ask`. Send one non-streaming request with a single user message and return the response object unchanged, so the caller can still read `stop_reason` and `usage`.
4. Implement `ask_streaming`. Iterate `stream_text` and join the deltas. Compare how the two feel when you run `main`.
5. Implement `usage_summary`. Read `input_tokens`, `output_tokens`, `cache_read_input_tokens`, and `cache_creation_input_tokens` defensively with `getattr`, defaulting each to 0, and add a `total_tokens` entry.
6. Implement `main` to print the masked key, the model, the non-streaming answer with its usage, and then the streaming answer as it arrives. Return 1 on `MissingAPIKeyError` and 0 otherwise.

## Verification

```bash
pytest labs/00-setup/tests -v
```

The offline tests cover key handling, masking, and usage parsing, and must pass with no API key set. The two tests that make live calls skip cleanly when `ANTHROPIC_API_KEY` is absent, and passing them means you got a real answer back with non-zero output tokens.

## Going further

- Set `max_tokens` to 16 and inspect `stop_reason`. Confirm that truncation is visible in the response rather than silent.
- Send the same prompt twice and compare `usage`. Then send it with a long system prompt and compare again.
- Time both call styles end to end, and time each to its first visible character. The gap between those two numbers is what streaming buys.

## Certification mapping

- **Anthropic, Building Effective Agents and Effective context engineering for AI agents**: The plain model call that the augmented LLM building block augments.
- **Databricks Generative AI Engineer Associate**: Application development including RAG and LLM chains.
- **NVIDIA NCA Generative AI LLMs**: LLM integration and deployment; Python libraries for LLMs.

Exam objectives change over time. Treat this as a pointer, not a syllabus, and check the official exam guides directly. See `docs/cert-mapping.md` for the full table.
