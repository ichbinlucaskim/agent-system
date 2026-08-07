# Lab 15 - Evaluation

## Goal

After this lab you can build a regression suite for an LLM system: deterministic assertions where they apply, rubric-based LLM-as-judge scoring where they do not, and a pass rate report across repeated runs rather than a single-run verdict.

## Prerequisites

Labs 00 through 06. Concepts: the evaluator from lab 06, and the fact that model output varies between runs.

## Estimated time

60 to 90 minutes

## Background

Without an evaluation suite, a prompt change is a guess. The output looks different, someone decides it looks better, and nobody can say whether the change fixed the case that motivated it or broke four cases nobody checked. An eval turns that into a number you can compare before and after.

Write deterministic assertions first, and write as many as you can. Does the JSON parse, is the required field present, is the citation id one that exists, is the answer under the length limit, does the refusal case actually refuse. These checks are free, unambiguous, and they catch most regressions.

Use a judge only for what cannot be asserted: tone, faithfulness to a source, whether an explanation is actually helpful. The judge is itself a model call and carries all the variance you are trying to measure, so give it a rubric with specific, independently gradeable criteria and ask for structured output rather than a verdict in prose. Collect judge scores alongside the deterministic results, but keep the suite pass rate deterministic only — mixing the two into one number hides which kind of variance moved.

Single-run results are noise. The same input can pass on one run and fail on the next, so run each case several times and report the pass rate. A case at three passes out of five is not a pass and not a failure: it is a flaky case, and knowing which cases are flaky is often more useful than the aggregate score.

Keep the failures. A report that says eighty percent is not actionable; a report that names the four cases that failed and shows what they returned is. Store the outputs so a regression can be diagnosed without re-running the whole suite. Judge parse failures belong in their own error section, never folded into a score of zero.

Grow the suite from real failures. Every bug someone reports becomes a case, and the suite stops being a synthetic benchmark and starts being a record of what has actually gone wrong in your system.

## Steps

1. Define `Case`: an id, the input, and the list of deterministic checks it must satisfy, so a case is data rather than a hand-written test function.
2. Implement `run_deterministic`: apply each check to an output and return per-check results with a reason for each failure.
3. Implement `judge`: score an output against a rubric with structured output, returning a score and the reason behind it.
4. Implement `run_suite`: run every case `runs` times, collect deterministic results (and judge results when a rubric is set), and keep the raw outputs. The pass rate is deterministic only.
5. Implement `format_report`: print a per-case pass rate, mark cases between 0 and 1 as flaky, list failures with their outputs, and list judge errors separately.
6. Change one behaviour in a scripted target, re-run the suite, and compare the two reports in `main`. That comparison is the point of the entire lab.

## Verification

```bash
pytest labs/track-4-production/15-evaluation/tests -v
```

The suite machinery is tested offline with stubbed outputs. Passing means a deterministic check reports its reason on failure, the pass rate is computed across runs rather than from the last run, a case that passes intermittently is marked flaky, the report names every failing case and shows its output, the suite wires an injected judge without folding scores into the pass rate, a judge response that does not parse is recorded as an error instead of scoring zero, and that error appears in the report.

## Going further

- Add a case for every bug you hit while doing labs 01 through 14. Real failures make better cases than invented ones.
- Run the judge twice on the same output and measure how often it disagrees with itself. That number bounds how much you should trust it.
- Split the report by category and find which kind of case regresses when you optimise for another.

## Certification mapping

- **Anthropic, Building Effective Agents and Effective context engineering for AI agents**: Evaluator-optimizer applied as an offline regression suite; measuring before optimising.
- **Databricks Generative AI Engineer Associate**: Evaluation and monitoring including custom scorers; governance.
- **NVIDIA NCA Generative AI LLMs**: Experimentation; data analysis and visualization; alignment.

Exam objectives change over time. Treat this as a pointer, not a syllabus, and check the official exam guides directly. See `docs/cert-mapping.md` for the full table.
