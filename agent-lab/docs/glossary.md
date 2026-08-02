# Glossary

Terms as this course uses them, with the lab where each one is built. Kept in
sync with `glossary.ko.md`.

## Core building blocks

**Augmented LLM** (lab 01)
A model call with retrieval, tools, and memory attached. The base building block
in Building Effective Agents. Every other pattern in this course is composed of
calls of this shape.

**Workflow** (labs 02 to 06)
A system where the control flow is written by you. The steps and their order are
in the code, so the behaviour is predictable and testable.

**Agent** (lab 12)
A system where the model decides what happens next, in a loop, until a stop
condition fires. The difference from a workflow is who chooses the next step,
and that difference is why an agent needs budgets.

**Tool** (labs 01, 07)
An action described to the model by a name, a description, and an input schema.
The model emits a `tool_use` block; your code executes it and returns a
`tool_result`. The model never executes anything itself.

**Tool result** (lab 01)
The output your code returns for a tool call, one per `tool_use` id, all in a
single user message. A failed tool returns a result marked as an error rather
than raising.

## Patterns

**Prompt chaining** (lab 02)
A fixed sequence of calls where each consumes the previous output, usually with
a programmatic gate between steps.

**Gate** (lab 02)
A deterministic check in ordinary code between two steps of a chain. It stops a
bad intermediate result from being paid for twice.

**Routing** (lab 03)
Classifying an input and dispatching it to one of several specialized prompts or
models, with a fallback route for input that fits none of them.

**Misroute rate** (lab 03)
The fraction of a labelled set that a classifier sends to the wrong route. It
requires labelled data, and without it a change to a classification prompt is a
guess.

**Sectioning** (lab 04)
Splitting one task into independent parts and running a call per part
concurrently.

**Voting** (lab 04)
Running the same task several times and aggregating the answers. Agreement is
evidence; disagreement is a signal to escalate.

**Orchestrator-workers** (lab 05)
A lead call that decomposes a task into subtasks it decides at runtime, worker
calls that execute them, and a lead call that synthesizes the result.

**Evaluator-optimizer** (lab 06)
A generator call paired with a critic call in a loop, with explicit stopping
criteria and a maximum iteration budget.

## Tools and context

**Agent-computer interface (ACI)** (lab 07)
The surface an agent sees: tool names, descriptions, schemas, and error
messages. It is to an agent what a user interface is to a person.

**Retrieval** (labs 01, 08)
Putting facts into the prompt at request time that the model does not otherwise
have.

**Chunking** (lab 08)
Splitting documents into retrievable pieces. Chunk size and overlap are the two
knobs, and lab 09 sweeps them rather than guessing.

**Embedding** (lab 08)
A vector representation of text used for similarity search. This course uses a
deterministic local hash-based stub so that no embedding API is required.

**Cosine similarity** (lab 08)
The similarity measure used by `common/vectorstore.py`. It compares direction
rather than magnitude, which is what you want when documents differ in length.

**Grounding** (lab 08)
Requiring an answer to come from provided passages, cite them, and refuse when
they do not support one.

**Recall at k** (lab 09)
Of the passages that should have been retrieved, the fraction that appeared in
the top k. The core retrieval metric, and it needs a labelled set.

**Hybrid search** (lab 09)
A weighted combination of keyword and vector scores. The two fail in different
directions, so the combination usually beats either alone.

**Reranking** (lab 09)
A second, more careful scoring pass over a cheaply retrieved shortlist.

**MCP-style server** (lab 10)
A tool server that speaks a documented protocol over stdio instead of being
imported as a function. The boundary buys isolation, independent deployment,
and runtime discovery.

**Context window** (lab 11)
The tokens the model sees on one request. Treat it as a budget: what is in it
costs money on every turn and dilutes what else is in it.

**Context engineering** (lab 11)
Deciding what occupies the window at each step, and what belongs in a summary or
in a file instead.

**Compaction** (lab 11)
Replacing older turns with a summary. It is lossy on purpose, so decide what is
load bearing before compacting.

**Scratchpad** (lab 11)
Notes written to a file with only a pointer kept in the window, so a run can
accumulate more than the window could hold.

## Autonomy and production

**Agent loop** (lab 12)
Send messages, run the requested tools, append the results, repeat. Almost all
the code you write around it is about when to stop.

**Step budget, cost ceiling, deadline** (lab 12)
Three independent limits on a run. They fail differently, so keep them separate
and report which one stopped a run.

**Non-progress detection** (lab 12)
Noticing that a run keeps repeating the same action and observation. A stuck
agent does not crash, so a step budget alone will let it spin.

**Subagent** (lab 13)
A child agent with its own context window and a restricted tool set. The win is
context isolation and capability restriction; the cost is the handoff.

**Approval gate** (lab 14)
A person standing between a `tool_use` block and its execution, shown enough of
the consequence to make a real decision.

**Action classification** (lab 14)
Sorting actions into automatic, needing confirmation, and forbidden, by
reversibility and blast radius, and enforcing that in code.

**Evaluation suite** (lab 15)
A set of cases run repeatedly, scored by deterministic checks where possible and
by a rubric-based judge where not, reported as a pass rate.

**LLM as judge** (lab 15)
Using a model call to score output against a rubric. It carries the same
variance it is measuring, so it needs specific criteria and structured output.

**Flaky case** (lab 15)
A case whose pass rate is strictly between 0 and 1. It is neither a pass nor a
failure, and knowing which cases are flaky is often more useful than the
aggregate.

**Trace** (lab 16)
A structured record per step, carrying name, duration, token usage, and error,
so cost and latency can be attributed to steps rather than runs.

**Guardrail** (lab 17)
Code that runs whether or not the model cooperates. A system prompt instruction
is a preference, not a control.

**Prompt injection** (lab 17)
Instructions aimed at the model, hidden in content the model reads. The usual
entry point is a tool result rather than the user's message.

**Smoke test** (lab 18)
The minimum deployment check: does it start, does it answer, does a malformed
request produce a clean error. It is not an evaluation of quality.

## API terms

**Token** (lab 00)
The unit of both cost and context budget. Note that `input_tokens` in a response
counts only the uncached remainder of the prompt.

**`stop_reason`** (lab 00)
Why generation ended. `tool_use` drives the tool loop; `max_tokens` means the
response was truncated; `refusal` means the request was declined.

**Streaming** (lab 00)
Receiving output as it is generated. It does not change the answer, only when
you see it, and it avoids HTTP timeouts on long responses.

**System prompt** (labs 00, 01)
Instructions and context placed ahead of the conversation. Retrieved passages
usually go here, labelled with their source.
