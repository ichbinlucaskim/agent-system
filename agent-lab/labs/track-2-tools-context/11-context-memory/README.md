# Lab 11 - Context and memory

## Goal

After this lab you can treat the context window as a budget you manage: estimate token cost, drop or compact history under a limit while protecting anchors, move bulk detail to a scratchpad file, and decide deliberately what stays in the window and what stays out.

## Prerequisites

Labs 00 through 08, especially the memory in lab 01. Concepts: token counting, and the difference between what a model needs and what it merely could use.

## Estimated time

45 to 60 minutes

## Background

Context engineering is deciding what occupies the window at each step. A large window makes this feel unnecessary, which is the trap: filling a window because it is available costs money on every turn, and dilutes the material that actually matters with material that merely might.

Useful context sits in three tiers. What must be in the window verbatim, because the model reasons over it right now. What can be compacted into a summary, because the gist is enough. What belongs outside the window entirely in a file, with only a pointer in the window. Most long-running agent context belongs in the third tier and ends up in the first by accident.

Budgeting means knowing what things cost. This lab uses a rough character-based token estimate, which is fine for making drop-or-keep decisions and is not fine for billing. When a number needs to be exact, count tokens with the API rather than estimating them.

Some parts of the context are anchors and must never be dropped: the system prompt, the task statement, and any constraint the model is being held to. A budgeter that trims purely by age will eventually drop the instruction that defines the job, and the failure looks like the model getting worse for no reason.

Compaction is lossy on purpose. Replacing ten turns with a summary is only safe if you have decided what is load bearing in those turns, which usually means identifiers, decisions, and constraints rather than prose. A good compaction keeps what a later step would have to ask about again.

A scratchpad is the third tier made concrete. The agent writes findings to a file, keeps a one-line pointer in the window, and re-reads the file only when it needs the detail. This is how a run can accumulate far more knowledge than the window could ever hold at once.

## Steps

1. Implement `estimate_tokens`: a rough character-based estimate, documented in the docstring as an estimate and not a billing number.
2. Implement `budget_messages`: drop oldest-first until the estimate fits a limit, while never dropping messages marked as anchors.
3. Implement `compact`: replace everything older than the most recent few turns with a summary that preserves identifiers, decisions, and constraints.
4. Implement `Scratchpad`: write, read, and list notes under `data/`, keeping the window content to a pointer rather than the note body.
5. Implement `build_context`: assemble anchors, the compacted summary, recent turns, and scratchpad pointers into a final message list that fits the limit.
6. Run the same conversation with and without budgeting, and compare total tokens against answer quality.

## Verification

```bash
pytest labs/track-2-tools-context/11-context-memory/tests -v
```

All of the budgeting logic runs offline. Passing means the budgeter never drops an anchor even when that means exceeding the limit, oldest non-anchor messages go first, compaction leaves the recent turns verbatim, the scratchpad survives a write and read round trip, and `build_context` returns a message list within the limit whenever one exists.

## Going further

- Compare dropping against compaction on a long conversation and note which questions each strategy makes unanswerable.
- Have the model write its own scratchpad notes and check whether its notes are the ones a later step actually needed.
- Compare your character estimate against real token counts from the API and record the error for your kind of text.

## Certification mapping

- **Anthropic, Building Effective Agents and Effective context engineering for AI agents**: Effective context engineering: token budgeting, compaction, and keeping detail outside the window.
- **Databricks Generative AI Engineer Associate**: Application development including LLM chains; governance.
- **NVIDIA NCA Generative AI LLMs**: Prompt engineering; software development; data preprocessing and feature engineering.

Exam objectives change over time. Treat this as a pointer, not a syllabus, and check the official exam guides directly. See `docs/cert-mapping.md` for the full table.
