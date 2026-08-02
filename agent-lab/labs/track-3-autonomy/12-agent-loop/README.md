# Lab 12 - The agent loop

## Goal

After this lab you can build an autonomous loop that runs until it is done or until a budget stops it: explicit stop conditions, a step budget, a cost ceiling, retries on tool error, and detection of a run that is no longer making progress.

## Prerequisites

Labs 00 through 07, and lab 06 for the shape of a bounded loop. Concepts: the tool-use loop, and the fact that autonomy is defined by its limits.

## Estimated time

60 to 90 minutes

## Background

This is the point where a workflow becomes an agent. In every earlier lab your code decided what happened next. Here the model decides, and it keeps deciding until a stop condition fires. That is the entire difference, and it is why everything in this lab is about limits.

The loop itself is short: send the messages, run any tools the model asked for, append the results, repeat. Almost all the code you actually write is about when to stop, and a loop with no ceiling is not an agent, it is an open-ended bill.

Give the loop several independent budgets, because they fail differently. A step budget bounds how many turns it may take. A cost ceiling bounds token spend, which a step budget does not, since one step can be far more expensive than another. A wall-clock deadline bounds latency for anything a person is waiting on. Whichever binds first should stop the run, and the run should report which one it was.

Tool failures are normal and are usually transient. Retry a failed tool once or twice, then return the error to the model as a tool result so it can choose a different approach. Distinguish the two clearly: a retry is you deciding to try again, and returning the error is the model deciding what to do next.

The hardest stop condition is non-progress. A stuck agent does not crash; it calls the same tool with the same arguments, gets the same result, and remains confident. Detect it by hashing recent action and observation pairs and stopping when the recent window is all repeats, because a step budget alone will let that spin for its whole allowance.

Whatever ends the run, the result must say why. A returned object carrying the answer, the stop reason, the step count, and the spend is the difference between an agent you can operate and one you can only restart.

## Steps

1. Define `AgentBudget`: a dataclass with `max_steps`, `max_usd`, and `max_seconds`, and a `RunState` that tracks steps taken, spend, and elapsed time.
2. Implement `is_exhausted`: return whether any budget is spent and which one, so the caller learns the reason and not just the fact.
3. Implement `run_tool_with_retry`: retry a failing tool a fixed number of times, then return the error as a tool result rather than raising.
4. Implement `detect_no_progress`: hash recent action and observation pairs and return True when the last few are all identical.
5. Implement `agent_loop`: run until the model stops asking for tools, a budget is exhausted, or non-progress is detected. Return the answer, the stop reason, the step count, and the spend.
6. Attach a `Trace` from `common.tracing` so each step is recorded, then print the report for a run that hits its budget.

## Verification

```bash
pytest labs/track-3-autonomy/12-agent-loop/tests -v
```

Every budget and detector is tested offline with a stubbed model. Passing means the loop stops at the step budget, stops at the cost ceiling before the step budget when spend is high, retries a failing tool the configured number of times and then surrenders to the model, detects a repeated action loop, and always returns a stop reason naming the condition that fired.

## Going further

- Give the model a task it cannot complete and watch which budget stops it. That is your real safety margin.
- Report the remaining budget to the model in each turn and see whether it prioritises differently as the budget shrinks.
- Make non-progress detection tolerant of a retry with different arguments, and check that you have not made it blind to a genuine loop.

## Certification mapping

- **Anthropic, Building Effective Agents and Effective context engineering for AI agents**: The autonomous agent loop and its stopping conditions; when to use an agent instead of a workflow.
- **Databricks Generative AI Engineer Associate**: Tool and agent frameworks; evaluation and monitoring.
- **NVIDIA NCA Generative AI LLMs**: Software development; LLM integration and deployment.

Exam objectives change over time. Treat this as a pointer, not a syllabus, and check the official exam guides directly. See `docs/cert-mapping.md` for the full table.
