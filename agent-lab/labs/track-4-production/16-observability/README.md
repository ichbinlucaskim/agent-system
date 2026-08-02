# Lab 16 - Observability

## Goal

After this lab you can record a structured trace for every step of a run, attribute cost and latency to individual steps rather than whole runs, and render a text report that shows where a run spent its budget.

## Prerequisites

Labs 12 and 15, and `common/tracing.py` and `common/cost.py`. Concepts: token usage as the unit of cost.

## Estimated time

45 to 60 minutes

## Background

This lab is marked optional because the labs before it work without it. It stops being optional the moment someone asks why a run cost what it cost, because a run total cannot answer that and a per-step trace can.

One record per step, and the record is structured data rather than a log line. Step name, inputs, output, duration, token usage, and error. Structured records can be summed, sorted, and grouped; log lines have to be parsed by whoever is on call at the time.

Attribute to steps, because that is the level at which you can act. A run that cost three times what you expected is not actionable. A run where the synthesis step carried eighty percent of the input tokens because it received every worker's full output is actionable immediately.

Latency and cost are different questions and often have different answers. The slowest step is frequently not the most expensive one, and optimising the wrong one is a common way to spend a week for nothing. Report both, side by side, per step.

Record failures with the same care as successes. A step that errored still consumed tokens and time, and a trace that only holds successful steps will systematically under-report the cost of a system that is retrying.

Keep the report as plain text. It works in a terminal, in CI output, and in a pull request comment, with no service to run and no dependency to add. When you later move to a hosted tracing product, the records you designed here map onto it directly.

## Steps

1. Extend the `StepRecord` from `common/tracing.py` with whatever your runs need, keeping every field summable or sortable.
2. Implement `trace_step`: wrap any callable so it records name, duration, usage, and error without the caller writing bookkeeping at each site.
3. Implement `attribute_cost`: convert per-step usage into per-step dollars with `common/cost.py`, and verify the parts sum to the whole.
4. Implement `slowest_steps` and `costliest_steps`: return the top n by each measure, since they are usually different steps.
5. Implement `render_report`: one line per step with duration, tokens, and cost, then totals, then the two top-n lists.
6. Run an orchestrator from lab 05 under the trace and identify the single step that dominates the bill.

## Verification

```bash
pytest labs/track-4-production/16-observability/tests -v
```

Tracing and attribution are pure bookkeeping and are tested offline. Passing means each step is recorded exactly once, a step that raised is still recorded with its error and its usage, per-step costs sum to the run total, and the report names every step so nothing is silently missing.

## Going further

- Compare a cached and an uncached run of the same task, and read the difference off the cache read tokens rather than the wall-clock time.
- Add a step budget warning that fires when one step exceeds a share of the run total, and choose that share deliberately.
- Emit the same records as JSON lines and confirm that everything the text report shows can be recomputed from them.

## Certification mapping

- **Anthropic, Building Effective Agents and Effective context engineering for AI agents**: Observability for agent runs; measuring context and cost per step.
- **Databricks Generative AI Engineer Associate**: Evaluation and monitoring including MLflow tracing; assembling and deploying applications.
- **NVIDIA NCA Generative AI LLMs**: Data analysis and visualization; software development; experimentation.

Exam objectives change over time. Treat this as a pointer, not a syllabus, and check the official exam guides directly. See `docs/cert-mapping.md` for the full table.
