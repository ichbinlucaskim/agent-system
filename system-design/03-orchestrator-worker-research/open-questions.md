# Open questions - 03 Orchestrator-worker research system

This case is unusually well sourced, which makes the remaining gaps sharper
rather than fewer. Most of them are about mechanism: the post says what the
system does and rarely how.

## Unknown mechanism

- **What does a subtask handed to a subagent actually contain?** We know the lead
  delegates specialized tasks and that subagents work in their own context
  windows. We do not know whether a subagent receives a natural language brief,
  a structured object, or a share of the lead's plan. This matters because it
  determines how much context transfer the pattern costs, which is the main
  argument for and against it. A worked example of a delegated task would answer
  it.

- **How are findings distilled, and by whom?** Findings come back distilled. It
  is not stated whether the subagent summarizes on its own initiative, follows
  an instruction, or fills a fixed output contract. This matters because the
  distillation step is where the attribution problem is created, and a fixed
  contract that carried source identifiers would change what the CitationAgent
  has to reconstruct. A description of the subagent return format would answer
  it.

- **What terminates the research loop?** The lead can spawn another wave or
  refine strategy, and nothing in our material says what stops it. This matters
  because an unbounded model-directed loop is exactly the shape that produced
  the reported failure of scouring the web endlessly. A documented stop
  condition or budget would answer it.

- **Where does checkpointing attach, and what is in a checkpoint?** Checkpointing
  is named as a production concern with no further detail. This matters because
  a checkpoint that captures the lead's plan is a very different recovery story
  from one that captures every subagent's window. A description of checkpoint
  contents would answer it.

- **How does the CitationAgent get the source documents?** It processes them
  alongside the report, so they are retained somewhere after the subagents that
  read them have finished. Our material does not say where. This matters because
  that store is the thing that makes attribution possible, and anyone copying
  the pattern has to build it. A description of source retention would answer
  it.

## Unknown magnitude

- **How many subagents does a healthy run use?** We know 50 for a simple query
  was wrong, and we do not know what right looks like, or whether the number is
  chosen per query or bounded globally. This matters because the fan-out width
  drives the token multiple. A distribution of subagent counts over real queries
  would answer it.

- **What does the 15x token multiple decompose into?** The figure covers
  multi-agent systems against chat interactions. We cannot tell how much is
  duplicated context across worker windows, how much is the extra coordination
  turns, and how much is the CitationAgent pass. This matters because the three
  have different remedies. Per-component token accounting would answer it.

- **What does the internal research eval measure?** The 90.2% improvement is
  quoted with the framing the post gives it and no more. Without knowing the
  task distribution or the scoring method, the number cannot be compared with
  anything else, including a reader's own system. Publication of the eval
  design, or its task distribution, would answer it.

## Disputed between sources

None. This case rests on a single first-party source, so there is nothing to
reconcile. That is a limitation rather than a strength: no outside party has
been consulted on whether the reported behavior reproduces.

## Deliberately out of scope

- **Whether 90.2% would replicate on a different eval.** This is a question about
  the evaluation rather than the architecture. It belongs with the paper topic
  `07-evaluation` in the sibling paper repository, and with lab exercise
  `15-evaluation`.

- **Whether a different orchestration topology would do better.** Star, chain,
  and peer-to-peer arrangements are a research question. This library's job is
  to describe what a named system does, not to propose alternatives.

- **How Memory is implemented.** The architectural fact that matters here is that
  the plan is written somewhere durable before truncation. The storage mechanism
  is an implementation question, and case `11-context-memory` in the lab is
  where that gets built rather than described.
