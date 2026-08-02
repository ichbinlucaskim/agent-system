# 07 - Workflow, not agent

## Representative system

None, deliberately. This case describes the design you should have ruled out
before any of the others in this library became relevant.

## Why this archetype exists

Every other case in this library is an argument for an agent. Read in sequence
they build a momentum that is not in the source material, and this case exists
to stop it.

[T1] Anthropic's Building Effective Agents draws the distinction directly:
workflows are systems where LLMs and tools are orchestrated through predefined
code paths, while agents are systems where LLMs dynamically direct their own
processes and tool usage. [T1] Its guidance is to find the simplest solution
possible and increase complexity only when needed, which may mean not building
an agentic system at all. [T1] Agentic systems trade latency and cost for better
task performance. [T1] Optimizing a single LLM call with retrieval and
in-context examples is often enough.

[T1] The follow-on post on multi-agent systems is blunter: teams have invested
months building elaborate multi-agent architectures only to discover that
improved prompting on a single agent achieved equivalent results.

What this case stresses that no other case does is **the decision not to
build**. Cases 01 through 06 answer "how should this agent be designed". This
one answers "should there be one", and it is the only question in the library
whose correct answer is frequently no.

### The checklist

Run this before reaching for an agent. Each item is a question with a preferred
answer, and a preferred answer means stop.

1. **Have you measured a single LLM call with retrieval and in-context
   examples?** [T1] states this is often enough. If the answer is no, you do not
   yet know what you are improving on, and any agent you build will be compared
   against nothing.
2. **Have you tried improving the prompt instead?** [T1] reports months of
   multi-agent work matched by better prompting on a single agent. This is the
   cheapest experiment available and the one most often skipped.
3. **Are the steps known in advance?** [T1] If they are, that is a workflow by
   definition, and a predefined code path gives you the same result with a stack
   trace when it breaks.
4. **Does the task divide into genuinely independent strands?** Case 03 shows
   [T1] that the multi-agent approach suits problems that divide into parallel
   strands and is less effective for tightly interdependent tasks such as
   coding. If the strands talk to each other, you are paying for isolation you
   cannot use.
5. **Can you afford the trade?** [T1] Agentic systems trade latency and cost for
   better task performance. That is a trade with two sides, and case 03 gives
   [T1] one measured magnitude for the cost side: roughly 15 times the tokens of
   a chat interaction.
6. **Do you have a way to tell whether it worked?** Case 04 shows what a design
   looks like when an oracle exists and case 03 shows what evaluation costs when
   it does not. Building an agent before you can evaluate one means you will not
   be able to tell whether step 2 would have sufficed.

[T1] The post does name conditions under which a verification subagent remains
worthwhile even given all of the above: when the orchestrator is less capable,
when verification needs specialized tools, or when an explicit verification
checkpoint is wanted. [T1] It also gives the reason they work, which is that
verification requires minimal context transfer by nature. [T3] Our reading is
that this last clause is the actual selection rule, and it generalizes: delegate
the parts of a task that need little context to be handed over, and keep the
parts that need a lot.

## The twelve dimensions

These describe a fixed pipeline. They are shorter than the other cases because
a workflow has less to say about most of them, and that brevity is the point.

### 1. Problem and success criteria

[T3] A task whose steps are known when the code is written. Success is defined
per stage as well as end to end, because each stage has a fixed input and output
contract that can be asserted on.

### 2. Autonomy level

[T1] Workflow: LLMs and tools orchestrated through predefined code paths. This
is the definitional end of the spectrum, and every other case in the library
sits somewhere to the other side of it.

### 3. Observation space

[T3] Fixed per stage and determined by the code. A stage sees what it was
passed. There is no exploration step, which removes both the ability to find
unexpected material and the ability to waste a budget looking for it.

### 4. Action space

[T3] Whatever the code calls, in the order the code calls it. The model
contributes text; it does not select actions. This is the dimension that makes
the safety questions in case 01 largely vanish, because a model that cannot
choose an action cannot choose a damaging one.

### 5. Tools and agent-computer interface

[T3] There is no tool-selection problem, because tools are invoked by the
program rather than chosen by the model. An entire failure class from case 01,
where a subagent is never called because its description does not say when to
call it, does not exist here. Interface design work shifts from describing tools
to a model, toward defining stage contracts for a compiler and a test suite.

### 6. Context strategy

[T3] Constructed per stage by the code, and bounded by construction. Nothing
accumulates unless the pipeline was written to accumulate it, so the context
strategies that cases 01 and 03 spend most of their design budget on are
replaced by a decision about what to pass forward.

### 7. Memory and state

[T3] Explicit. State is whatever the pipeline carries between stages, held in
ordinary program variables or storage, visible in the source, and testable.

### 8. Control flow

[T1] Predefined code paths. This is the definition of the archetype and the
source of every other property in this list.

[T3] Our reading is that this is the dimension worth deciding first. A failure
in a workflow has a line number, and a failure in an agent has a transcript.

### 9. Error handling and recovery

[T3] Ordinary software error handling: exceptions, retries, timeouts, and
whatever the language and framework already provide. A failed stage fails in a
way an on-call engineer has seen before.

### 10. Human involvement and permissions

[T3] Wherever the code puts a person, deterministically. An approval step in a
workflow runs every time, in the same place, which is a stronger guarantee than
any of the permission machinery in case 01 because there is no mode in which the
model routes around it.

### 11. Evaluation

[T3] Per stage and end to end. A fixed pipeline can be tested stage by stage,
with fixtures, in the way ordinary software is tested. No case in this library
with model-directed control flow can do that, which is a considerable and
routinely underweighted advantage.

### 12. Cost and latency budget

[T1] Agentic systems trade latency and cost for better task performance. [T3]
Our reading of the converse: the workflow keeps the latency and the cost, and
gives up the task performance on inputs its author did not anticipate. That is
the whole trade, stated in one line, and it is worth being able to say which
side of it you are choosing and why.

## Failure modes

All [T3], reasoned from the archetype.

- **The case the code path does not cover.** A workflow handles the inputs its
  author imagined. An unanticipated input does not produce an adaptive attempt;
  it produces a wrong answer through a path that was never meant for it.
- **Silent degradation as the input distribution drifts.** The pipeline keeps
  running and keeps returning results, and the stage that no longer suits the
  data does not announce itself. An agent failing on the same drift is often
  noisier and therefore noticed sooner.
- **Ossification.** Each new case adds a branch. After enough branches the
  predefined code path is a decision tree that nobody understands, and the
  original advantage, that a failure has a line number, has been spent.
- **Being right for the wrong reason.** A workflow chosen because it was simpler
  and retained because it works can outlive the constraint that made it correct,
  and the review that would catch this is the same checklist above, run again.

## One thing to steal

Measure the single-call baseline before designing anything.

[T1] Optimizing a single LLM call with retrieval and in-context examples is
often enough, and [T1] teams have discovered after months that improved
prompting on a single agent achieved equivalent results to an elaborate
multi-agent architecture. [T3] Our reading is that the load-bearing word in both
sentences is comparative: these are claims about a baseline, and a team that
never built the baseline cannot make the comparison and therefore cannot know
which of the two situations it is in. The baseline is also the cheapest artifact
in the entire process, which is what makes skipping it hard to defend.

## One thing not to copy

The fixed pipeline, applied to a genuinely open-ended task.

[T3] Our reading is that this case is as easy to over-apply as the ones it
argues against. The predefined code path is correct when the steps are knowable
and becomes a liability at exactly the point where enumerating cases stops being
possible, which is the ossification failure above seen early. The checklist runs
in both directions: the question is not whether agents are overused in general
but whether this task's steps are knowable, and a confident no is as much an
answer as a confident yes.

## Related

**Lab exercises:** `02-prompt-chaining`, `03-routing`, `01-augmented-llm`,
`15-evaluation`, `04-parallelization`.

**Paper topics:** `01-reasoning`, `05-multi-agent`, `07-evaluation`.

**Other cases:** this case is the counter-argument to
`03-orchestrator-worker-research` specifically, and the checklist above should
be run before adopting anything from `01-terminal-coding-agent`.
