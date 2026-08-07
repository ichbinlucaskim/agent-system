# Lab 11 - Context and memory

## Goal

After this lab you can treat the context window as a budget you manage: estimate token cost, drop or compact history under a limit while protecting anchors, move bulk detail to a scratchpad file the model can still reach, and decide deliberately what stays in the window and what stays out.

## Prerequisites

Labs 00 through 08, especially the memory in lab 01 and the tool design in lab 07. Concepts: token counting, and the difference between what a model needs and what it merely could use.

## Estimated time

45 to 60 minutes

## Background

Context engineering is deciding what occupies the window at each step. A large window makes this feel unnecessary, which is the trap: filling a window because it is available costs money on every turn, and dilutes the material that actually matters with material that merely might.

Useful context sits in three tiers. What must be in the window verbatim, because the model reasons over it right now. What can be compacted into a digest, because the gist is enough. What belongs outside the window entirely in a file, with only a pointer in the window. Most long-running agent context belongs in the third tier and ends up in the first by accident.

Budgeting means knowing what things cost. This lab uses a rough character-based token estimate, which is fine for making drop-or-keep decisions and is not fine for billing. When a number needs to be exact, count tokens with the API rather than estimating them.

Some parts of the context are anchors and must never be dropped: the system prompt, the task statement, and any constraint the model is being held to. A budgeter that trims purely by age will eventually drop the instruction that defines the job, and the failure looks like the model getting worse for no reason.

Anchors are only half of that lesson, and the other half is easy to miss. **Cut in order of value, not in order of age.** The digest that replaced twenty older turns is, by construction, the oldest non-anchor message in the window, so a budgeter that drops the oldest thing first will throw the digest away and keep the small talk that came after it. That inverts the whole point of compacting: the identifiers, decisions, and constraints you carefully preserved go first, and pleasantries survive verbatim. Give each message a tier and sacrifice raw turns before compressed ones.

Compaction is lossy on purpose. Replacing ten turns with a digest is only safe if you have decided what is load bearing in those turns, which usually means identifiers, decisions, and constraints rather than prose. A good compaction keeps what a later step would have to ask about again. It also needs a size cap rather than a hope: an extractive summary that keeps whole sentences will, on a history where nearly every sentence carries an identifier, produce something longer than what it replaced. Compaction that saves nothing is pure loss, so a compactor that cannot beat the turns it is replacing should decline to run at all. For the same reason, do not compact a history that already fits.

A scratchpad is the third tier made concrete. The agent writes findings to a file, keeps a one-line pointer in the window, and reads the file only when it needs the detail. This is how a run can accumulate far more knowledge than the window could ever hold at once, and it only works if the pointer is actionable: it has to name the note, say how large it is so the model can judge whether opening it is worth the tokens, and come with a tool that opens it. A pointer with no way to follow it is not a tier, it is a dead end.

Two consequences of trimming catch people out because they show up as errors that look unrelated to the budget. The first is mechanical: dropping an assistant turn from between two user turns leaves two user messages in a row, and dropping the first user turn can leave the list starting with an assistant message. Both are the budgeter's doing, so normalising them belongs with the budgeter rather than in a retry after the API complains. The second is stranger and worth seeing for yourself. A history trimmed by age alone opens mid-thread, with decisions already asserted and an assistant already agreeing to them, which is indistinguishable from a planted conversation designed to make a model accept a false premise; a model can decline to answer such a context outright. The digest happens to fix this as well, because it declares what it stands in for instead of leaving a silent gap.

Which brings up the last point, about measurement. When you compare answers across contexts, an empty answer is not a bad answer. A refusal, or a run that ended on `max_tokens`, has nothing to do with what was in the window, and scoring it as a context failure sends you tuning the budget to fix something the budget did not cause. Read `stop_reason` before drawing a conclusion.

## Steps

1. Implement `estimate_tokens` and `total_tokens`: a rough character-based estimate, documented in the docstring as an estimate and not a billing number.
2. Implement `budget_messages`: never drop a message marked as an anchor, and drop everything else by tier, oldest first within a tier, so raw turns are sacrificed before the digest. Finish with a pass that can drop any remaining non-anchor message, or a typo in a tier name pins something in the window forever.
3. Implement `compact`: replace everything older than the most recent few turns with a digest that preserves identifiers, decisions, and constraints, tagged with the digest tier. Cap its size, and decline to compact when the digest would not be smaller than what it replaced.
4. Implement `Scratchpad` and `scratchpad_index`: write, read, and list notes under `data/`, and build a pointer that names each note, its size, and the tool that opens it.
5. Implement `build_context`: assemble anchors, the digest, recent turns, and scratchpad pointers into a message list that fits the limit, skipping compaction entirely when the raw history already fits.
6. Implement `to_api_messages`, `READ_NOTE_TOOL`, `run_read_note`, and `answer_with_scratchpad`: normalise the shape budgeting broke, and let the model open the notes it decides it needs.
7. Ask one question whose answer needs a fact from early history and a fact that only lives in a note, then answer it from three contexts: everything in the window, a trim by age alone, and the budgeted context. Compare token cost against whether each answer actually contains the two facts.

## Verification

```bash
pytest labs/track-2-tools-context/11-context-memory/tests -v
```

All of the budgeting logic runs offline, and the one test involving a model stubs it, because what is under test is which context reached it.

Passing means the budgeter never drops an anchor even when that means exceeding the limit, raw turns are sacrificed before the digest while the digest is still droppable when nothing else is left, an unrecognised tier does not make a message immortal, compaction leaves the recent turns verbatim and never costs more than the turns it replaced, a digest asked to fit a target fits it, a pointer names its note along with the note's size and the tool that reads it, the scratchpad survives a write and read round trip and rejects a name that escapes its directory, `build_context` returns a list within the limit, keeps note bodies out of the window, and leaves a fitting history uncompacted, the bookkeeping fields never reach the API, consecutive same-role turns are merged and a leading assistant turn is dropped, a bad note name comes back as an error naming the real options, the model can follow a pointer to detail that was never in the window, and an empty answer reports its `stop_reason` rather than passing for a bad one.

Running `main` needs a key only for the final comparison, and prints a clear skip message without one, so the budgeting half of the lab stays runnable offline.

## Going further

- Compare dropping against compaction on a long conversation and note which questions each strategy makes unanswerable.
- Watch which turns survive verbatim in the demo. Recency is a cheap stand-in for relevance, and the chit-chat that survives while decisions get compressed is what that approximation costs. Fixing it properly means letting a model judge importance, which puts a model call inside your budgeter.
- Have the model write its own scratchpad notes and check whether its notes are the ones a later step actually needed.
- Compare your character estimate against real token counts from the API and record the error for your kind of text. Then note what the estimate ignores entirely: tool definitions, system prompts, and images all occupy the same window.
- Take the naive trim from the demo and prepend a digest opener to it. If the model refused the trimmed context and accepts the same content once the gap is declared, you have found the difference between a context that is smaller and a context that looks forged.

## Certification mapping

- **Anthropic, Building Effective Agents and Effective context engineering for AI agents**: Effective context engineering: token budgeting, compaction, and keeping detail outside the window.
- **Databricks Generative AI Engineer Associate**: Application development including LLM chains; governance.
- **NVIDIA NCA Generative AI LLMs**: Prompt engineering; software development; data preprocessing and feature engineering.

Exam objectives change over time. Treat this as a pointer, not a syllabus, and check the official exam guides directly. See `docs/cert-mapping.md` for the full table.
