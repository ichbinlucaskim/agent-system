# Lab 17 - Guardrails

## Goal

After this lab you can defend an agent at its boundaries: filter what comes in, validate what goes out against a schema, treat tool results as untrusted data rather than instructions, and refuse out-of-scope requests in code rather than by asking the model nicely.

## Prerequisites

Labs 01, 07, 12, and 14. Concepts: the tool loop, and where untrusted content enters a system.

## Estimated time

45 to 60 minutes

## Background

A guardrail is code that runs whether or not the model cooperates. An instruction in a system prompt is a strong preference and nothing more, and everything in this lab exists because a preference is not a control.

Input filtering is the cheap layer. Cap the length, reject content types you do not handle, and stop obviously out-of-scope requests before they cost a call. It catches accidents and volume, and it will not stop a determined attacker, which is why it is only the first layer.

Output validation is where you decide what your system is allowed to emit. If a downstream consumer expects an object with three fields, validate it against a schema and fail loudly on a mismatch, rather than passing a shape that will break something two services away.

The dangerous input is usually not the user's message. It is the tool result: a web page, a database row, a file, an email. Any of those can contain text addressed to the model, and if your prompt does not distinguish data from instructions, the model has no way to either.

The mitigation is structural. Wrap untrusted content in a clearly labelled block that names its source and states that its contents are data and never instructions, then restrict what the agent can do while holding it. Detection heuristics that scan for phrases like ignore previous instructions are worth adding, but they are a tripwire and not a wall.

Scope refusal needs both halves. Tell the model what it does not handle, and also check in code, because a refusal you can only get by asking is a refusal an injection can take away.

## Steps

1. Implement `check_input`: enforce a length cap and an allowed-topic check, and return `(ok, reason)` so a rejection can be explained to the caller.
2. Implement `validate_output`: check a parsed payload against a small schema and return every violation, not just the first one.
3. Implement `wrap_untrusted`: place tool results inside a labelled block naming the source and stating that its content is data and never instructions.
4. Implement `detect_injection`: flag known instruction-like patterns in tool results, and document in the docstring that this is a tripwire and not a defence.
5. Implement `guarded_answer`: run the input filter, make the call with wrapped tool results, validate the output, and return the answer together with every guardrail decision.
6. Feed the agent a document containing an embedded instruction and confirm that the tool restriction, not the prompt, is what stops it.

## Verification

```bash
pytest labs/track-4-production/17-guardrails/tests -v
```

Every guardrail here is deterministic and tested offline, which is the point: a guardrail you cannot test is a hope. Passing means oversized and out-of-scope input is rejected with a reason, schema validation reports all violations at once, untrusted content is labelled with its source, known injection phrasings are flagged, and the result carries the guardrail decisions alongside the answer.

## Going further

- Write five injection attempts that your detector misses, then decide which are actually stopped by the tool restrictions anyway.
- Move the schema check to the tool result as well as the final output, and note which failures that catches earlier.
- Measure how often a legitimate request trips the input filter. A guardrail with a high false-positive rate will be turned off by someone.

## Certification mapping

- **Anthropic, Building Effective Agents and Effective context engineering for AI agents**: Guardrails at the agent-computer interface; treating tool results as untrusted data.
- **Databricks Generative AI Engineer Associate**: Governance; application development including RAG and LLM chains.
- **NVIDIA NCA Generative AI LLMs**: Alignment; prompt engineering; software development.

Exam objectives change over time. Treat this as a pointer, not a syllabus, and check the official exam guides directly. See `docs/cert-mapping.md` for the full table.
