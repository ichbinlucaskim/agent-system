# Sources - 07 Workflow, not agent

## Tier definitions as used in this library

- **T1 first-party**: official documentation, the vendor's own engineering
  writing, papers by the system's authors, or public source code.
- **T2 second-party**: credible outside analysis or reverse engineering.
- **T3 inference**: our own reasoning, always phrased as our reading.

## T1

**Anthropic, "Building Effective Agents".** Backs the definitional distinction
and the guidance that frames the whole case:

- Workflows are systems where LLMs and tools are orchestrated through predefined
  code paths, while agents are systems where LLMs dynamically direct their own
  processes and tool usage.
- The guidance is to find the simplest solution possible and increase complexity
  only when needed, which may mean not building an agentic system at all.
- Agentic systems trade latency and cost for better task performance.
- Optimizing a single LLM call with retrieval and in-context examples is often
  enough.

**Anthropic, "When to use multi-agent systems (and when not to)", claude.com
blog.** Backs checklist items 2 and the verification-subagent carve-out:

- Teams have invested months building elaborate multi-agent architectures only
  to discover that improved prompting on a single agent achieved equivalent
  results.
- Verification subagents remain valuable when the orchestrator is less capable,
  when verification needs specialized tools, or when an explicit verification
  checkpoint is wanted, and they work because verification requires minimal
  context transfer by nature.

**Borrowed T1, cited to their own case folders.** Checklist items 4 and 5 use
two facts sourced in `03-orchestrator-worker-research/sources.md`: that the
multi-agent approach suits problems dividing into parallel strands and is less
effective for tightly interdependent tasks such as coding, and that multi-agent
systems use roughly 15 times more tokens than chat interactions. They are marked
[T1] here because they are first-party in their home case, and the source entry
lives there rather than being duplicated.

## T2

None.

## T3

- **The twelve dimensions**, apart from 2, 8, and the first half of 12, which
  are T1. The rest is our description of what a fixed pipeline implies, and it
  is deliberately unremarkable: these are properties of ordinary software, not
  discoveries.
- **"Minimal context transfer is the actual selection rule"** (checklist
  closing). Reasoning from the T1 clause that verification subagents work
  because verification requires minimal context transfer by nature. Generalizing
  that clause into a rule for what to delegate is ours.
- **The workflow-versus-agent diagram pair** in `architecture.md`. Reasoning
  from the T1 definitions.
- **All four failure modes.** Reasoned from the archetype. Ossification and
  silent degradation in particular are common software experience rather than
  anything reported about LLM pipelines specifically, and they are labelled as
  our reading.
- **"The workflow keeps the latency and cost and gives up task performance on
  unanticipated inputs"** (dimension 12). Reasoning from the T1 statement of the
  trade, read in the other direction. The T1 sentence states what agentic
  systems trade away; the converse is ours.

## Deliberately excluded

- **Any claim about how often teams over-build.** The T1 material says teams have
  done this. It does not quantify it, and this case does not either, despite the
  temptation to write something like "most teams".
- **Any performance comparison between workflows and agents.** Not in our
  material. The case argues for measuring the baseline rather than asserting
  what the measurement will show.
- **A named example of a system that should have been a workflow.** Naming one
  would require sourced material about a specific team's decision, and it would
  be uncharitable on top of being unsourced.
