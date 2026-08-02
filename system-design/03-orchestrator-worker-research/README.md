# 03 - Orchestrator-worker research system

## Representative system

Anthropic Research, as described in the engineering post "How we built our
multi-agent research system".

## Why this archetype exists

This is the case where the work does not fit in one context window and cannot be
made to. Case 01 delegates for permission and specialization; case 04 works
inside a repository that a single agent can navigate. Here the input is the open
web, the amount of material that could be read is unbounded, and the output is a
single document that has to be internally consistent.

What this case stresses, and nothing else here does, is **delegation as a
context strategy**. Every other case treats subagents, when it uses them at all,
as a way to parallelize or to restrict capability. This one shows what happens
when a fresh context window is the point, and what breaks downstream when the
coordinating agent ends up holding only summaries of what its workers read.

## The twelve dimensions

### 1. Problem and success criteria

Open-ended research producing a report whose claims are attributed to sources.

[T1] The post defines a multi-agent system as multiple agents, meaning LLMs
autonomously using tools in a loop, working together. [T1] It states the
approach suits problems that divide into parallel strands and is less effective
for tightly interdependent tasks such as coding.

There is no machine-checkable oracle. [T1] Evaluation combined LLM judging with
human review, which is what a problem without an oracle forces. This is the
sharpest contrast in the library with case 04, where a test suite decides.

### 2. Autonomy level

Agent, at the model-directed end. [T1] A lead agent coordinates while delegating
specialized tasks to subagents operating in parallel, in an orchestrator-worker
pattern. [T1] The lead agent decides whether more research is needed and can
spawn another wave or refine strategy, so neither the number of steps nor the
number of workers is fixed in advance.

### 3. Observation space

[T1] Subagents search independently, each with its own context window, and
return distilled findings.

[T3] Our reading is that the lead agent and its workers have different
observation spaces, and that this is deliberate rather than incidental. The
workers observe raw sources. The lead observes worker summaries. By the time the
lead drafts, it has never seen most of the material the report rests on.

### 4. Action space

Externally read-only. [T1] The documented actions are searching, returning
findings, spawning further work, and producing a report. [T1] The lead writes
its plan to Memory.

[T3] Our reading is that the absence of an irreversible external side effect is
why this case spends almost none of its design budget on permissions, and why
case 01 spends most of its budget there. The two systems are both agents with
model-directed control flow, and they differ on this dimension more than any
other.

### 5. Tools and agent-computer interface

[T1] Subagents are the primary delegation mechanism, and a separate
CitationAgent processes the source documents and the research report to identify
where citations belong, so that claims are attributed.

[T3] Our reading is that the CitationAgent is the most interesting object in
this architecture, and that it exists as a consequence of dimension 3. The lead
agent, by the time it drafts, is working from summaries of summaries and cannot
verify attribution against anything it still holds. Attribution therefore has to
be reconstructed by a separate pass that goes back to the original documents.
The citation problem is created by the context strategy, and then solved by
another agent.

### 6. Context strategy

This is the dimension the case exists for.

[T1] Subagents search independently, each with its own context window, and
return distilled findings. [T1] The LeadResearcher thinks through the approach
and saves its plan to Memory to persist context, because if the context window
exceeds 200,000 tokens it will be truncated and the plan must survive.

[T3] Our reading, and the analytical point of this case: subagents here are a
context-management primitive before they are a parallelism primitive. The
parallelism is a benefit, but a system that ran the same subagents one after
another would still need them, because the alternative is one window holding
everything every worker read. The saved plan is the same idea applied to the
lead itself, treating its own context as unreliable storage.

### 7. Memory and state

[T1] Memory holds the lead agent's plan across the truncation boundary. [T1]
Checkpointing is named among the production concerns.

[T3] Our reading is that these are two different durability problems solved
separately: Memory protects a specific artifact from context truncation within a
run, while checkpointing protects the run from process failure. A design that
conflates them tends to discover the difference during an incident.

### 8. Control flow

Model-directed, in waves. [T1] The lead agent decides whether more research is
needed and can spawn another wave or refine strategy.

[T1] Early agents spawned 50 subagents for simple queries, and prompt
engineering was the primary lever for fixing behaviors of this kind.

[T3] Our reading is that this is the honest version of a familiar tradeoff.
Model-directed fan-out is what makes the system able to size its own effort to
the question, and it is also what allows it to size that effort wrongly by two
orders of magnitude. The reported fix was prompting rather than a hard cap,
which is a different choice from the one case 01 makes with `maxTurns`.

### 9. Error handling and recovery

[T1] Production concerns named in the post include checkpointing, retry logic,
and rainbow deployments.

[T3] Our reading is that this list describes a long-running stateful system
rather than a request-response one. Rainbow deployments in particular are a
response to runs that outlive a deploy, which is a problem case 02 does not have
and case 01 has in a different form.

### 10. Human involvement and permissions

No human is documented inside the run loop. [T1] Human review appears in
evaluation, where reviewers caught issues such as overreliance on SEO-optimized
sources.

[T3] Our reading is that the read-only action space is what makes an unattended
loop acceptable here. There is no action a person needs to approve, because
nothing the system does is hard to undo. Compare case 06, where the loop
contains a user by design, and case 01, where the loop must be gated because its
actions bite.

### 11. Evaluation

[T1] Evaluation combined LLM judging with human review. [T1] Human reviewers
caught issues such as overreliance on SEO-optimized sources. [T1] A multi-agent
system with Claude Opus 4 as lead agent and Claude Sonnet 4 subagents
outperformed single-agent Claude Opus 4 by 90.2% on their internal research
eval.

[T3] Our reading of the SEO finding is that it is the most useful sentence in
the post for anyone building an evaluation. It is a failure that an LLM judge is
poorly placed to catch, because the judge sees the same well-formed sources the
system did, and it was found by a human looking at inputs rather than outputs.

### 12. Cost and latency budget

[T1] Multi-agent systems use roughly 15 times more tokens than chat
interactions. [T1] The reported configuration used Claude Opus 4 as lead agent
and Claude Sonnet 4 subagents.

[T3] Our reading is that the model split is a direct cost response to dimension
6. Workers do bounded, well-specified reading in their own windows, which is the
part of the work most amenable to a smaller model, while the lead holds the
strategy. The 15x figure is what makes that split worth engineering rather than
a detail.

## Failure modes

The first three are [T1], reported in the post as behaviors of early versions,
not inferred by us.

- **Fan-out sized to nothing in particular.** [T1] Early agents spawned 50
  subagents for simple queries.
- **Searching for sources that do not exist.** [T1] Early agents scoured the web
  endlessly for nonexistent sources.
- **Workers distracting each other.** [T1] Early agents distracted each other
  with excessive updates.
- **Fit failure on interdependent work.** [T1] The approach is less effective
  for tightly interdependent tasks such as coding. [T3] Our reading is that this
  is the same property as dimension 6 seen from the other side: independent
  context windows are an advantage exactly when the subtasks are independent,
  and a liability when workers need to know what the others found.
- **Attribution drift.** [T3] Our reading, from the existence of the
  CitationAgent rather than from any reported incident: a drafting agent working
  from distilled findings can produce a claim it cannot trace, and the failure
  is invisible in the draft because a confident sentence and an attributable
  sentence look the same.

[T1] The post reports that prompt engineering was the primary lever for fixing
the first three.

## One thing to steal

The CitationAgent shape: a separate pass that returns to the original sources to
attach attribution, run after drafting rather than during it.

[T3] Our reading of why this generalizes: any system that summarizes on the way
in will have an agent that drafts from material it can no longer see. Asking
that agent to also cite correctly is asking it to verify against something it
does not hold. Splitting attribution into its own pass with its own access to
the originals is the structural fix, and it applies to any pipeline with a
summarization step, whether or not it is multi-agent.

## One thing not to copy

The fan-out itself, for tightly interdependent work. [T1] The post is explicit
that the approach suits problems that divide into parallel strands and is less
effective for tightly interdependent tasks such as coding, and [T1] that it
costs roughly 15 times the tokens of a chat interaction.

[T3] Our reading is that these two facts should be read together as a single
condition rather than as separate caveats. The token multiplier buys parallel
coverage of independent strands. When the strands are not independent, the
multiplier is still charged and the thing it was buying is not delivered. Case
07 exists in this library to give that check a place to live.

## Related

**Lab exercises:** `05-orchestrator-workers`, `13-subagents`,
`04-parallelization`, `11-context-memory`, `15-evaluation`.

**Paper topics:** `05-multi-agent`, `04-memory-and-retrieval`, `07-evaluation`.

**Other cases:** `07-workflow-not-agent` is the deliberate counter-argument to
this one. `01-terminal-coding-agent` uses subagents for a different reason.
