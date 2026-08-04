# Lab 04 - Parallelization

## Goal

After this lab you can run model calls concurrently in the two useful shapes: sectioning, which splits independent subtasks across calls, and voting, which runs the same task several times and aggregates the answers.

## Prerequisites

Labs 00 through 03. Concepts: independent versus dependent subtasks, and Python's `concurrent.futures`.

## Estimated time

45 to 60 minutes

## Background

Parallelization applies when subtasks do not depend on each other. If step two needs step one's output, that is a chain and belongs in lab 02. If the subtasks can be answered in any order, running them concurrently turns a sum of latencies into a maximum of latencies.

Sectioning splits one task into independent parts, runs a call per part, and merges the results. Reviewing a document for correctness, tone, and legal risk is three separate readings, and giving each its own call means each gets a focused prompt and a full budget of attention instead of one call dividing itself three ways.

Voting runs the same task several times and aggregates. It works because model output varies between runs, so agreement across runs is evidence and disagreement is a signal to escalate. It is well suited to judgments with a small answer space, such as is this safe, does this compile, is this a duplicate.

Aggregation is a design decision, not an afterthought. Majority wins is the obvious rule, but unanimity is the right rule when a false positive is expensive, and any-yes is right when a missed detection is expensive. Report the agreement level alongside the answer so the caller knows how much the votes actually agreed.

Concurrency in Python costs almost nothing here, because the work is network-bound rather than CPU-bound. A `ThreadPoolExecutor` is sufficient. What does cost is money and rate limit: N votes means N times the tokens, and a wide fan-out can trip a rate limit that a serial version never would.

## Steps

1. Implement `section`: split a review task into a fixed list of independent aspects, each with its own instruction.
2. Implement `run_sections`: run one call per section concurrently with a `ThreadPoolExecutor`, and return results in the original section order regardless of completion order.
3. Implement `merge_sections`: combine the section results into one report, keeping each section labelled rather than blending them into prose.
4. Implement `vote`: run the same question n times concurrently and return both the answers that came back and the errors from the calls that did not.
5. Implement `majority`: return the most common answer together with the fraction of votes that agreed, breaking ties deterministically so the same votes always give the same result.
6. Add a concurrency cap and handle a failed call by recording the error rather than losing the whole batch. This applies to both shapes: a section keeps its slot, and a lost vote costs one vote while agreement is measured over the votes that arrived.

## Verification

```bash
pytest labs/track-1-patterns/04-parallelization/tests -v
```

Aggregation and ordering are deterministic and tested offline. Passing means sectioning preserves order under out-of-order completion, majority picks the modal answer and reports the agreement fraction, ties resolve the same way every time, and one failed call does not lose the other results in either shape.

## Going further

- Measure wall-clock time for the serial and concurrent versions of the same sectioned task, and compare it against the extra token spend.
- Change the aggregation rule from majority to unanimity on a safety-style question and describe which errors each rule trades away.
- Increase the vote count from three to seven and check whether agreement rises enough to justify more than double the cost.

## Certification mapping

- **Anthropic, Building Effective Agents and Effective context engineering for AI agents**: Parallelization in both variants: sectioning and voting.
- **Databricks Generative AI Engineer Associate**: Problem decomposition and solution design; evaluation and monitoring.
- **NVIDIA NCA Generative AI LLMs**: Software development; experimentation.

Exam objectives change over time. Treat this as a pointer, not a syllabus, and check the official exam guides directly. See `docs/cert-mapping.md` for the full table.
