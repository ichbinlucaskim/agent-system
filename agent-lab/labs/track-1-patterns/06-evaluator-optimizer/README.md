# Lab 06 - Evaluator and optimizer

## Goal

After this lab you can pair a generator call with a critic call in a loop, define explicit stopping criteria, bound the loop with a maximum iteration budget, and return the best draft rather than the last one.

## Prerequisites

Labs 00 through 05. Concepts: structured output, and the idea that a critique is only useful if it is specific.

## Estimated time

45 to 60 minutes

## Background

This pattern applies when you can articulate what good looks like better than you can produce it in one shot. A generator produces a draft, an evaluator scores it against explicit criteria and says what is wrong, and the generator tries again with that feedback. Translation, code that must pass tests, and writing to a style guide all fit.

The evaluator needs criteria specific enough to grade independently. Asking whether a draft is good yields noise. Asking whether it names every requirement, stays under two hundred words, and avoids the passive voice yields a score you can act on and a critique the generator can use.

Feedback must be threaded back into the next generation. If the second call does not see the critique, the loop is just resampling, and you would be better served by the voting pattern from lab 04, which at least runs the samples concurrently.

Every loop needs two exits: a success condition and a budget. Stop when the score clears the target, and stop unconditionally at the maximum iteration count. Without the second exit, a task the model cannot satisfy will consume tokens until something else breaks.

Track the best draft seen, not just the most recent one. Scores do not increase monotonically, and a third iteration can be worse than the second. Returning the highest-scoring draft along with its score and iteration number makes the loop's behaviour visible and its output defensible.

## Steps

1. Write `CRITERIA` as a list of specific, independently gradeable checks. Vague criteria are the usual reason this pattern fails.
2. Implement `generate`: produce a draft, optionally taking previous feedback as an additional instruction.
3. Implement `evaluate`: score the draft against the criteria and return structured output with a score, a pass flag, and per-criterion feedback.
4. Implement `is_done`: return True when the score clears the target or when the iteration budget is exhausted, and say which condition fired.
5. Implement `refine`: run the loop, thread feedback into the next generation, keep the best draft seen, and return it with its score, its iteration, and the stop reason.
6. Print the score history so a run that plateaus or regresses is visible at a glance.

## Verification

```bash
pytest labs/track-1-patterns/06-evaluator-optimizer/tests -v
```

The stopping logic is tested offline with a stubbed evaluator. Passing means the loop exits on a passing score, exits at the budget when no score ever passes, returns the best draft rather than the last, and threads the previous critique into the next generation.

## Going further

- Give the evaluator a different model from the generator and see whether the critiques get sharper.
- Replace half the criteria with deterministic Python checks and note which ones no longer need a model call at all.
- Log the score at each iteration across twenty runs and find the iteration count past which the average stops improving. That number is your real budget.

## Certification mapping

- **Anthropic, Building Effective Agents and Effective context engineering for AI agents**: Evaluator-optimizer: a generator and critic loop with explicit stopping criteria.
- **Databricks Generative AI Engineer Associate**: Evaluation and monitoring including custom scorers; application development.
- **NVIDIA NCA Generative AI LLMs**: Prompt engineering; alignment; experimentation.

Exam objectives change over time. Treat this as a pointer, not a syllabus, and check the official exam guides directly. See `docs/cert-mapping.md` for the full table.
