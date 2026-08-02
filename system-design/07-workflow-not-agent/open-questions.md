# Open questions - 07 Workflow, not agent

This case makes a recommendation, which makes its unknowns more consequential
than a descriptive case's. A reader is being told to run a checklist, and these
are the things we cannot tell them.

## Unknown mechanism

- **What does the checklist cost to run honestly?** Item 1 asks for a measured
  single-call baseline with retrieval and in-context examples. That is itself a
  build, with its own retrieval design and its own eval, and we present it as
  the cheap option without knowing what it costs relative to the agent it is
  meant to forestall. This matters because a checklist that is more expensive
  than the decision it informs will not be run. A worked account of building a
  baseline before an agent, with both efforts measured, would answer it.

- **How do you tell "the steps are known in advance" from "we have not
  discovered the steps yet"?** Checklist item 3 turns on this distinction and
  offers no test for it. This matters because it is the item most likely to be
  answered wrongly and confidently, in both directions. A set of worked examples
  where the initial judgement was later reversed would answer it.

- **What is the migration path when a workflow stops being sufficient?**
  Ossification is named as a failure mode with no account of what to do about
  it. Rewriting a mature pipeline as an agent is a substantial undertaking, and
  whether it can be done incrementally is unknown to us. Case studies of that
  transition would answer it.

- **Where exactly is the boundary of the verification-subagent carve-out?** [T1]
  names three conditions under which a verification subagent stays worthwhile.
  We do not know whether these are illustrative or exhaustive, and the
  difference matters to anyone using the list as a decision procedure. Further
  first-party guidance would answer it.

## Unknown magnitude

- **How much task performance does a workflow actually give up?** Dimension 12
  states the trade in both directions and quantifies neither side. The T1
  material states that agentic systems trade latency and cost for better task
  performance without a magnitude for the performance term. This matters because
  the whole checklist is a cost-benefit argument being made without one of the
  two numbers. A comparison on a fixed task, with both designs built, would
  answer it.

- **How often is the single-call baseline sufficient?** [T1] says it is often
  enough. We have no distribution, and "often" is doing a lot of work in an
  argument that leans on it. Any published rate would answer it.

- **At what branch count does a pipeline become harder to reason about than an
  agent?** The ossification failure mode implies a crossover point exists. We
  have no idea where it is, and it is likely to be team-specific rather than
  universal.

## Disputed between sources

None among our sources, which agree because they share an author organization.

[T3] Worth naming as a limitation rather than a strength: this case's argument
against over-building agents rests entirely on material published by a company
that sells access to models. That is not a reason to discount it, and the
material is specific and self-critical in a way that supports its credibility.
It is a reason to want an independent version of the same claim, and we do not
have one.

## Deliberately out of scope

- **How to design a good pipeline.** This is ordinary software architecture and
  is far better covered elsewhere. This case's job is the decision to build one,
  not the building.

- **Whether the workflow-agent distinction is the right taxonomy.** It is the
  taxonomy our T1 material uses and the one this library is organized around.
  Arguing with it belongs in a different document than the one that applies it.

- **The economics of the trade at a specific price point.** Prices change, and
  this library does not record figures that are not in its source material.
  Readers should run item 5 of the checklist against their own current numbers.
