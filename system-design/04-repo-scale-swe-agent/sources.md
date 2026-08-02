# Sources - 04 Repo-scale SWE agent

Every tier tag in this case folder resolves to an entry here.

## Tier definitions as used in this library

- **T1 first-party**: official documentation, the vendor's own engineering
  writing, papers by the system's authors, or public source code.
- **T2 second-party**: credible outside analysis or reverse engineering.
- **T3 inference**: our own reasoning from a T1 or T2 fact, always phrased as
  our reading.

## T1

**SWE-agent, arXiv 2405.15793.** Yang, Jimenez, Wettig, Lieret, Yao,
Narasimhan, Press. Agent-computer interfaces enable automated software
engineering.

What this backs in `README.md`: the identity of the representative system, and
the thesis quoted in dimension 5 that the agent-computer interface is what
enables the result. Note that this is the paper's framing as stated in its
title. We have the claim and not the design that supports it.

**SWE-bench, arXiv 2310.06770.** Jimenez, Yang, Wettig, Yao, Pei, Press,
Narasimhan.

What this backs, and it is the bulk of the sourced content in this case:

- An evaluation framework of 2,294 software engineering problems drawn from real
  GitHub issues and corresponding pull requests across 12 popular Python
  repositories.
- Given a codebase and an issue description, the model edits the codebase to
  address the issue.
- Resolving these issues frequently requires coordinating changes across
  multiple functions, classes, and files, interacting with execution
  environments, processing long contexts, and reasoning beyond traditional code
  generation.

## T2

None. No second-party analysis was used for this case.

## T3

Our inferences, each with the sourced fact it reasons from.

- **Success is machine-checkable and a test suite is the oracle** (dimensions 1
  and 11, and the premise of the whole case). Reasoning from problems being
  drawn from issues together with their corresponding pull requests. The
  resolution mechanism itself is not in our material, and this inference is
  flagged in the text everywhere it is load-bearing.
- **The system runs a loop rather than a single pass** (dimension 2). Reasoning
  from the task requiring interaction with execution environments, plus the
  authors naming it an agent.
- **Observation is an act of selection** (dimension 3). Reasoning from a
  repository exceeding any context window combined with long contexts being
  named as a demand.
- **The action space is the same as case 01's in kind and different in setting**
  (dimension 4). Reasoning from the edits taking place inside an evaluation
  harness over 2,294 instances, which is not a setting where a working tree is
  at risk.
- **Error handling and evaluation are the same machinery at different scopes**
  (dimension 9). Reasoning from execution environments returning observations
  produced by the agent's own actions.
- **No human is in the benchmark loop** (dimension 10). Reasoning from the
  instance count.
- **The construction of the benchmark is the transferable contribution**
  (dimension 11, and the "one thing to steal"). Reasoning from instances being
  drawn from already-completed and already-reviewed work.
- **All three failure modes.** Each names its T1 basis inline. None is reported
  in our material; all are reasoned from the stated demands of the task.

## Deliberately excluded

- **Any description of the agent-computer interface.** This is the most
  tempting gap in the case, because the paper's title asserts the interface is
  decisive and a reader will expect the interface to be described. Writing a
  plausible one from general knowledge of such systems would be exactly the
  failure this library is designed to prevent.
- **Any resolution rate, score, or leaderboard position.** No such figure
  appears in our material. Dimension 11 quotes the benchmark's size and
  construction and reports no results.
- **Any claim about how SWE-agent performs relative to other systems.** Not in
  our material.
- **The loop structure, tool inventory, context strategy, memory, and stop
  condition.** Dimensions 6, 7, and 8 are correspondingly short. They say what
  is not known rather than filling the space.
- **Any statement about non-benchmark use.** The material describes a benchmark
  setting, so claims about human involvement are scoped to that setting
  explicitly.
