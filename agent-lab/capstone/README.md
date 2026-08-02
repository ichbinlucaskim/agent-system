# Capstone - A bounded research agent

## Goal

Build one agent that uses everything the course covered, and defend its design
with numbers. The deliverable is not a demo. It is an agent with an evaluation
suite, a cost and latency report, an approval gate, and a written argument for
why each pattern in it is there.

## Prerequisites

Labs 00 through 18. Labs 09, 16, and 18 are marked optional in the course, but
the capstone assumes all three: without 09 you cannot defend your retrieval,
without 16 you cannot explain your cost, and without 18 you have a script rather
than a system.

## Estimated time

Six to ten hours, best spread over several sittings.

## The brief

Build an agent that answers questions about a document corpus you choose, and
that can act on its answers through at least one tool with a side effect.

Pick a corpus you actually care about. A project's own documentation, a set of
policies, a research area, your own notes. Fifty to five hundred documents is
the right size: enough that retrieval matters, small enough to label by hand.

The agent must be able to do something, not only answer. Writing a summary file,
opening an issue, sending a draft, updating a record. The action is what makes
the approval gate real rather than decorative.

## Requirements

**Architecture.** Use at least three patterns from track 1, and write down why
each is there. A routing step that sends factual questions down a cheap path and
analytical ones down an expensive one. A chain with a gate where a bad
intermediate result would be expensive. An evaluator-optimizer loop where you
can say what good looks like. The reasoning matters more than the count: a
pattern you cannot justify should be removed.

**Retrieval.** Chunk and embed your corpus with the local stub from lab 08.
Label at least twenty queries with the chunks that should answer them, and
report recall at k for your final configuration against at least one baseline
you rejected.

**Tools.** At least three tools, one of which has a side effect. Write the
descriptions as lab 07 taught: say when to call each tool, not only what it
does. Expose at least one of them through the MCP-style server from lab 10.

**Autonomy.** An agent loop with a step budget, a cost ceiling, and non-progress
detection. Every run returns a stop reason, including the successful ones.

**Human in the loop.** Classify every action into automatic, needing
confirmation, and forbidden. Enforce forbidden in code. Show a diff or an
equivalent consequence preview before any write.

**Context.** Handle a conversation longer than your context budget. Compaction,
a scratchpad, or both. Say which you chose and what it loses.

**Guardrails.** Input filtering, output validation against a schema, and tool
results wrapped as untrusted data. Include at least one test that feeds the
agent a document containing an instruction aimed at the model, and demonstrate
that the tool restrictions rather than the prompt are what stop it.

**Evaluation.** At least fifteen cases, deterministic checks wherever they
apply, a rubric-based judge only where they do not. Report pass rate across at
least three runs per case, and mark the flaky ones.

**Observability.** A trace per run, cost and latency attributed per step, and a
text report. Identify the step that dominates your bill and say what you did
about it.

**Packaging.** A CLI and a health endpoint. Configuration entirely from the
environment, validated at startup. A smoke test that proves it starts and
answers.

## Milestones

1. **Corpus and labels.** Collect the documents and write the labelled query
   set. Do this first: everything downstream is measured against it.
2. **Retrieval baseline.** Build the store, measure recall at k, try one
   alternative configuration, and keep the numbers for both.
3. **The augmented call.** Retrieval plus tools plus memory, answering with
   citations. This is lab 01 at full size.
4. **Patterns.** Add the track 1 patterns your task actually needs, one at a
   time, measuring after each.
5. **The loop.** Turn the workflow into an agent with budgets and stop reasons.
6. **Safety.** Approval gates and guardrails, with tests.
7. **Evaluation and observability.** The suite, the trace, the reports.
8. **Packaging.** CLI, health, smoke test, and a README a colleague could
   follow.

## Verification

There is no test harness for the capstone. The check is whether you can answer
these questions with evidence rather than opinion:

- What does one run cost, and which step dominates it?
- What is your retrieval recall at k, and what configuration did you reject?
- What is your pass rate, and which cases are flaky?
- What happens when a document tells the agent to ignore its instructions?
- What stops a run that is not making progress, and how do you know?
- Which pattern in your architecture could you remove without losing anything?

The last question is the important one. A design you can defend includes knowing
what is not carrying its weight.

## Going further

- Run the whole suite against two different models and compare quality per
  dollar rather than quality alone.
- Give the agent a task it cannot complete and confirm it stops cleanly, reports
  why, and leaves nothing half-written.
- Hand the repository to someone else and watch them set it up from your README
  without asking you anything.

## Certification mapping

The capstone touches every area the course maps to, because it assembles all of
them into one system.

- **Anthropic, Building Effective Agents and Effective context engineering for
  AI agents**: composing workflow patterns, agent loops, agent-computer
  interface design, and context engineering into one application.
- **Databricks Generative AI Engineer Associate**: problem decomposition and
  solution design; data preparation and chunking; application development
  including RAG and LLM chains; tool and agent frameworks including MCP servers;
  assembling and deploying applications; governance; evaluation and monitoring.
- **NVIDIA NCA Generative AI LLMs**: prompt engineering; alignment;
  experimentation; data analysis and visualization; data preprocessing and
  feature engineering; software development; Python libraries for LLMs; LLM
  integration and deployment.

Exam objectives change over time. Treat this as a pointer, not a syllabus, and
check the official exam guides directly. See `docs/cert-mapping.md`.
