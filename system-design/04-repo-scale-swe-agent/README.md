# 04 - Repo-scale SWE agent

## Representative system

SWE-agent, evaluated on SWE-bench.

> A note on evidence density. This case rests on two papers, and what we have of
> them here is their framing of the problem rather than their description of the
> solution. That is enough to characterize the archetype and not enough to
> describe the system's internals. Dimensions 5 through 8 are correspondingly
> thin, and the gaps are recorded in `open-questions.md` rather than filled in
> with plausible detail.

## Why this archetype exists

This is the one case in the library where success is machine-checkable.

[T3] Our reading: a test suite is an oracle, and that single fact removes the
evaluation problem that dominates every other case here. Case 03 needs LLM
judges and human reviewers because nothing can automatically decide whether a
research report is good. Case 01 hands the diff to a developer. Case 06 has a
policy that a human has to interpret. Here the question "did it work" has an
answer that a machine can produce, repeatedly, at low cost.

What follows from that is most of the design. An oracle makes retry loops
rational, makes evaluation a build step rather than a research project, and
makes it reasonable to let the agent run unattended over a repository, because
the check at the end is trustworthy. This case exists to isolate that variable:
it is close enough to case 01 in action space to make the comparison clean, and
it differs from it almost entirely because of the oracle.

## The twelve dimensions

### 1. Problem and success criteria

[T1] SWE-bench is an evaluation framework of 2,294 software engineering problems
drawn from real GitHub issues and corresponding pull requests across 12 popular
Python repositories. [T1] Given a codebase and an issue description, the model
edits the codebase to address the issue.

[T3] Our reading is that success is machine-checkable, which is the premise of
the whole case. We should be precise about the limits of our evidence here: our
material states that the problems are drawn from issues and their corresponding
pull requests, and does not state the mechanism by which a candidate edit is
judged to resolve an issue. The inference that the paired pull request supplies
a checkable criterion is ours. See `open-questions.md`.

### 2. Autonomy level

Agent rather than workflow. [T1] The system is named an agent by its authors and
the task requires interacting with execution environments, which implies a loop
rather than a single pass.

Our material does not describe the loop's structure, its bounds, or its stop
condition, so we do not describe them.

### 3. Observation space

[T1] The agent observes a codebase and an issue description. [T1] Resolving these
issues frequently requires interacting with execution environments and
processing long contexts.

[T3] Our reading is that this is the richest observation space in the library and
also the most expensive one. A repository is larger than any context window, so
observation here is necessarily an act of selection, and the quality of that
selection is a design problem rather than a retrieval detail.

### 4. Action space

[T1] The model edits the codebase to address the issue. [T1] Resolving issues
frequently requires coordinating changes across multiple functions, classes, and
files.

[T3] Our reading is that this action space is nominally the same as case 01's,
file mutation, and practically very different, because it takes place against a
disposable checkout inside an evaluation harness rather than against a
developer's working tree. The edits are reversible by discarding the instance.
That is why this case spends nothing on permission architecture and case 01
spends most of its budget there, and it is worth being explicit that the
difference is the setting rather than the capability.

### 5. Tools and agent-computer interface

[T1] The claim in the paper's title is that agent-computer interfaces enable
automated software engineering.

That is the thesis, and our material does not contain the interface design that
supports it. We are not going to reconstruct what the interface consists of. The
transferable part of the claim is its shape: that the interface an agent is
given is a primary determinant of what it can accomplish, rather than a wrapper
around capabilities the model already has. See `open-questions.md`, which lists
this as the largest gap in the case.

### 6. Context strategy

[T1] Processing long contexts is named as one of the demands of the task.

Our material does not describe how the system manages context. Given that a
repository exceeds any window, there is a strategy here, and we cannot source
it.

### 7. Memory and state

Not described in our material.

### 8. Control flow

Not described in our material beyond what dimension 2 states.

### 9. Error handling and recovery

[T1] Resolving these issues frequently requires interacting with execution
environments.

[T3] Our reading is that this is the dimension where this case differs most
usefully from the rest of the library, because the environment answers back. A
test run or a stack trace is an observation produced by the agent's own action,
which means error handling and evaluation are the same machinery operating at
different scopes. Case 02 has nothing equivalent, and case 03's workers get no
signal of this kind from a search result.

### 10. Human involvement and permissions

[T3] Our reading is that there is no human in the loop during a benchmark run,
by construction: an evaluation over 2,294 instances is not one a person
supervises. Our material does not describe how the system is used outside the
benchmark setting, and we do not extend the claim there.

### 11. Evaluation

This is the case's defining dimension and the one our material actually
supports.

[T1] SWE-bench is an evaluation framework of 2,294 software engineering problems
drawn from real GitHub issues and corresponding pull requests across 12 popular
Python repositories. [T1] Resolving them frequently requires coordinating
changes across multiple functions, classes, and files, interacting with
execution environments, processing long contexts, and reasoning beyond
traditional code generation.

[T3] Our reading is that the construction is the contribution. The benchmark is
assembled from work that was already done and already reviewed, which means the
task distribution is real rather than authored, and the criterion comes with
each instance rather than being written by a benchmark designer. That is a
repeatable recipe, and it is the thing worth taking from this case.

### 12. Cost and latency budget

Nothing in our material addresses cost or latency for this system. No figures
are given here.

## Failure modes

All [T3], reasoned from the T1 characterization of what the task demands rather
than from reported results. Our material does not report failure analysis.

- **Localization failure.** [T1] states that resolving these issues frequently
  requires coordinating changes across multiple functions, classes, and files.
  [T3] Our reading is that an agent can produce a locally correct edit in the
  wrong place, and that this failure passes every check a model can run on its
  own output while failing the oracle.
- **Context exhaustion before the edit.** [T1] names processing long contexts as
  a demand of the task. [T3] Our reading is that observation competes with the
  work: budget spent reading the repository is budget unavailable for the edit
  and the test cycle.
- **Overfitting to the oracle.** [T3] Our reading, and the risk that comes free
  with having a checkable criterion: an agent that can run tests can write code
  that satisfies tests, which is not the same as code that resolves the issue.
  The oracle that makes this case tractable is also the thing it can be gamed
  against, and no other case in this library has that exposure because no other
  case has the oracle.

## One thing to steal

The benchmark construction, not the agent.

[T1] SWE-bench is built from real GitHub issues and their corresponding pull
requests. [T3] Our reading is that this is a recipe rather than a dataset: any
team with a bug tracker and a version control history already holds the raw
material for an evaluation set in which the tasks are real, the distribution is
theirs rather than a benchmark designer's, and the acceptance criterion for each
task was written by whoever fixed it. Most teams building an agent write their
eval cases by hand and get a smaller, more artificial set for more effort.

## One thing not to copy

The assumption that your domain has an oracle.

[T3] Our reading is that this is the most common way to misapply this case.
Almost every design decision here is downstream of automatic verification, so
the architecture reads as clean and confident, and it transfers to research
writing, customer support, or analytics only by giving up the property that made
it work. The correct move when there is no oracle is to design for review, as
case 03 does with human evaluation and case 06 does by keeping the user in the
loop, rather than to adopt this shape and hope a judge model substitutes.

## Related

**Lab exercises:** `15-evaluation`, `07-tool-design-aci`, `12-agent-loop`,
`06-evaluator-optimizer`.

**Paper topics:** `06-environment-and-interface`, `07-evaluation`,
`02-acting-and-tools`.

**Other cases:** the contrast with `01-terminal-coding-agent` is the point of
this case. `03-orchestrator-worker-research` shows what evaluation costs when
the oracle is absent.
