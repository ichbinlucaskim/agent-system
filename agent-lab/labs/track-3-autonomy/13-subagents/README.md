# Lab 13 - Subagents

## Goal

After this lab you can delegate a bounded task to a child agent that has its own context window and a restricted tool set, and you can compare a single-agent run against a subagent run on the same task to see what delegation actually costs and buys.

## Prerequisites

Labs 05 and 12. Concepts: the agent loop, context isolation, and the orchestrator pattern.

## Estimated time

45 to 60 minutes

## Background

A subagent is a child agent run with its own fresh context window, its own system prompt, and a tool set narrower than its parent's. The parent hands it a task description and gets back a report. Everything the subagent read along the way stays in its context and never enters the parent's.

Context isolation is the main reason to do this. A search that reads forty files and returns one paragraph costs the parent one paragraph instead of forty files. The parent stays coherent over a long run precisely because the exploration happened somewhere else.

The narrower tool set is the second reason and is often the more important one. A subagent that only needs to read can be given only read tools, so a prompt injection inside a document it reads has no write tool available to abuse. Restricting capability by construction beats instructing the model not to use it.

Delegation is not free. Each subagent re-establishes its own context from scratch, produces a report, and the parent then reads that report. For work the parent could finish in a few tool calls, that overhead exceeds the benefit, and the honest answer is to do it directly.

The useful shape is fan-out over genuinely independent work: several files to inspect, several candidates to check, several sources to consult. Sequential work with a shared thread of reasoning belongs in the parent, because splitting it means paying the handoff cost at every step.

This lab ends in a measurement, not an opinion. Run the same task both ways, and record total tokens, wall-clock time, and answer quality for each. The result is usually less lopsided than either the enthusiasts or the sceptics expect, and it will depend on your task.

## Steps

1. Define `SubagentSpec`: a dataclass with a name, a system prompt, an allowed tool name list, and a step budget.
2. Implement `restrict_tools`: return only the tool definitions the spec allows, and raise on a name the parent does not have. Capability is granted by construction, not by instruction.
3. Implement `run_subagent`: run the agent loop from lab 12 with the spec's own prompt, restricted tools, and a fresh message list that contains no parent history.
4. Implement `single_agent`: solve the same task in one agent with all tools and no delegation, as the comparison baseline.
5. Implement `with_subagents`: fan out over independent subtasks, run their subagents concurrently, and have the parent read only the reports.
6. Implement `compare`: run both approaches on one task and return total tokens, wall-clock time, and the answers side by side.

## Verification

```bash
pytest labs/track-3-autonomy/13-subagents/tests -v
```

Tool restriction and context isolation are structural properties and are tested offline. Passing means a subagent receives only its allowed tools, requesting a tool the parent lacks raises rather than silently passing through, the subagent's message list contains none of the parent's history, and `compare` reports token totals for both approaches.

## Going further

- Run the comparison on a task with two independent parts and again on a strictly sequential task. The second is where delegation should lose.
- Give a subagent a document containing an instruction aimed at the model, and confirm that the restricted tool set makes it harmless. That is lab 17 previewed.
- Vary the number of parallel subagents and find the point where added coordination stops paying for itself.

## Certification mapping

- **Anthropic, Building Effective Agents and Effective context engineering for AI agents**: Orchestrator-workers taken to the agent level; capability restriction as design.
- **Databricks Generative AI Engineer Associate**: Tool and agent frameworks; problem decomposition and solution design.
- **NVIDIA NCA Generative AI LLMs**: Software development; experimentation.

Exam objectives change over time. Treat this as a pointer, not a syllabus, and check the official exam guides directly. See `docs/cert-mapping.md` for the full table.
