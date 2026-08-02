# Lab 05 - Orchestrator and workers

## Goal

After this lab you can build a workflow where a lead call plans and decomposes a task dynamically, worker calls execute the subtasks, and the lead synthesizes the results, and you can explain how this differs from parallelization.

## Prerequisites

Labs 00 through 04. Concepts: concurrency, structured output, and the distinction between a fixed plan and a generated one.

## Estimated time

45 to 60 minutes

## Background

The distinguishing feature of this pattern is that the subtasks are not known in advance. In parallelization you decide the sections when you write the code. Here the lead call reads the task and decides what the subtasks are, which is what makes the pattern suitable for open-ended work such as researching a topic or changing code across files you have not seen.

That flexibility is exactly what makes it riskier. A generated plan can be empty, enormous, redundant, or nonsense. Treat the plan as untrusted input: validate its shape, cap the number of subtasks, drop duplicates, and reject entries missing required fields, before spending a single worker call on it.

Workers should be narrow. Each one receives a subtask description and only the context that subtask needs, not the entire conversation. Narrow context is what keeps worker calls cheap and keeps one subtask's noise from contaminating another's answer.

Synthesis is a real step, not a concatenation. The lead reads the worker outputs and produces the answer to the original task, resolving contradictions between workers and dropping what turned out to be irrelevant. If your synthesis step is just string joining, you have built sectioning with extra steps.

Cost grows quickly here: one planning call, N worker calls, one synthesis call, and the synthesis prompt contains all of the worker output. Cap the worker count, and log the plan alongside the result so that an expensive run can be explained afterwards.

## Steps

1. Implement `plan`: one lead call that reads the task and returns a list of subtasks as structured data, each with an id and a description.
2. Implement `validate_plan`: reject entries missing fields, drop duplicates, and truncate to `max_subtasks`. A generated plan is untrusted input.
3. Implement `run_worker`: execute one subtask with a narrow system prompt and only the context that subtask needs, returning the result plus the subtask id.
4. Implement `orchestrate`: plan, validate, run the workers concurrently with a cap, and synthesize. Return the plan, the worker results, and the final answer.
5. Implement `synthesize`: a final lead call that answers the original task from the worker outputs and resolves contradictions between them.
6. Make a worker failure non-fatal: record the error against that subtask and let synthesis proceed with what succeeded.

## Verification

```bash
pytest labs/track-1-patterns/05-orchestrator-workers/tests -v
```

Plan validation and orchestration control flow are tested offline against a stubbed planner. Passing means a malformed plan is rejected rather than executed, the subtask cap holds, a failing worker does not abort the run, and the returned result contains the plan so an expensive run can be explained.

## Going further

- Run the same task as sectioning from lab 04 with a hand-written plan, and compare quality and cost against the generated plan.
- Let a worker request one additional subtask, capped, and observe how quickly a self-extending plan grows.
- Give workers a smaller model than the lead and measure what that costs in final quality.

## Certification mapping

- **Anthropic, Building Effective Agents and Effective context engineering for AI agents**: Orchestrator-workers: a lead call that decomposes dynamically and synthesizes worker output.
- **Databricks Generative AI Engineer Associate**: Problem decomposition and solution design; tool and agent frameworks.
- **NVIDIA NCA Generative AI LLMs**: Prompt engineering; software development.

Exam objectives change over time. Treat this as a pointer, not a syllabus, and check the official exam guides directly. See `docs/cert-mapping.md` for the full table.
