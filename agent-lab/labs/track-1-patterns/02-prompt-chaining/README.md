# Lab 02 - Prompt chaining

## Goal

After this lab you can decompose a task into a fixed sequence of model calls where each call consumes the previous output, place a programmatic gate between steps, and decide when chaining is worth its extra cost and latency.

## Prerequisites

Labs 00 and 01. Concepts: the augmented call, system prompts, and the difference between control flow you write and control flow the model chooses.

## Estimated time

30 to 45 minutes

## Background

Prompt chaining decomposes a task into a fixed sequence of steps, where each model call handles one step and consumes the output of the one before it. The sequence lives in your code, not in the model's judgment, which makes the whole workflow predictable, debuggable, and cheap to test.

The trade is deliberate: you spend latency and tokens to buy accuracy. A single call asked to extract requirements, draft a specification, and polish the prose will do all three adequately. Three calls each doing one thing will usually do each of them better, because each call has one instruction set and one output format to satisfy.

The gate is what makes a chain more than a pipeline. Between two steps, run a deterministic check in ordinary Python: is the list non-empty, does the JSON parse, does the draft mention every requirement. If the check fails you stop, retry that step, or route elsewhere, instead of feeding a bad intermediate result into the next call and paying for it twice.

Errors compound along a chain. Three steps that are each right ninety percent of the time give a chain that is right about seventy three percent of the time. Gates are how you stop that multiplication, because a caught failure becomes a retry rather than a corrupted final answer.

Chaining is the wrong tool when one call already does the job. Each extra step multiplies cost, latency, and failure surface. Reach for a chain when the subtasks are genuinely different in kind, when you need a checkpoint in the middle, or when one giant prompt has started contradicting itself.

## Steps

1. Implement `extract_requirements`: one model call that turns a free-form brief into a list of short requirement strings.
2. Implement `gate_requirements`: a deterministic check returning `(ok, reason)`. Reject an empty list, a list of one vague entry, and entries that are not actionable.
3. Implement `draft_spec`: a second call that consumes only the gated requirement list, not the original brief.
4. Implement `polish_spec`: a third call that rewrites the draft for clarity without adding requirements.
5. Implement `run_chain`: run the three steps in order, apply the gate after step one, retry the failed step up to `max_retries`, and return every intermediate output so a failure is inspectable.
6. Wire a `Trace` from `common.tracing` through the chain and print the report so each step's tokens and latency are visible.

## Verification

```bash
pytest labs/track-1-patterns/02-prompt-chaining/tests -v
```

The gate tests run offline and are the core of this lab: a gate you cannot test deterministically is not a gate. The chain tests confirm that every intermediate output is returned, that a failed gate stops the chain, and that a retry happens exactly once.

## Going further

- Measure the chain against a single call that does all three steps at once, on the same ten briefs, and compare cost against quality.
- Make the gate call a model instead of plain Python, then argue for or against that choice on cost and reliability grounds.
- Add a branch: when the gate fails twice, route to a clarifying question instead of retrying a third time.

## Certification mapping

- **Anthropic, Building Effective Agents and Effective context engineering for AI agents**: Prompt chaining: decomposing a task into a fixed sequence with programmatic gates.
- **Databricks Generative AI Engineer Associate**: Problem decomposition and solution design; application development including LLM chains.
- **NVIDIA NCA Generative AI LLMs**: Prompt engineering; software development.

Exam objectives change over time. Treat this as a pointer, not a syllabus, and check the official exam guides directly. See `docs/cert-mapping.md` for the full table.
