# Architecture - 04 Repo-scale SWE agent

## Shape

Our material supports drawing the task and evaluation shape. It does not support
drawing the agent's internals, and the diagram says so rather than filling the
box.

```text
   one SWE-bench instance
   +--------------------------------------------------+
   |  [T1] a codebase                                  |
   |  [T1] an issue description                        |
   |                                                   |
   |  drawn from a real GitHub issue and its           |  [T1]
   |  corresponding pull request, across 12 popular    |
   |  Python repositories, 2,294 problems in total     |
   +--------------------------------------------------+
                          |
                          v
   +--------------------------------------------------+
   |                                                   |
   |   SWE-agent                                       |
   |                                                   |
   |   [T1] the paper's thesis is that agent-computer  |
   |        interfaces enable automated software       |
   |        engineering                                |
   |                                                   |
   |   ####  INTERNALS NOT SOURCED  ####               |
   |   The loop structure, the tool set, the context   |
   |   strategy, and the stop condition are not in     |
   |   our material. This box is deliberately empty.   |
   |   See open-questions.md.                          |
   |                                                   |
   +--------------------------------------------------+
             |                             ^
             | [T1] edits the codebase     | [T1] interacting with execution
             |      to address the issue   |      environments
             v                             |
   +--------------------------------------------------+
   |  execution environment                            |
   +--------------------------------------------------+
                          |
                          v
   +--------------------------------------------------+
   |  resolution judgement                             |
   |                                                   |
   |  [T3] our reading: machine-checkable, with the    |
   |       paired pull request supplying the criterion |
   |  the actual mechanism is NOT in our material      |
   +--------------------------------------------------+
```

## Flow

1. [T1] An instance presents a codebase and an issue description.
2. [T1] The model edits the codebase to address the issue.
3. [T1] Resolving frequently requires coordinating changes across multiple
   functions, classes, and files, interacting with execution environments,
   processing long contexts, and reasoning beyond traditional code generation.
4. [T3] Our reading: steps 2 and 3 repeat, because interacting with an execution
   environment implies acting on what the environment returned. Our material
   does not describe the iteration or what ends it.
5. [T3] Our reading: the result is judged automatically. The mechanism is not in
   our material.

## Boundaries

**Agent to execution environment.** [T1] The task requires interacting with
execution environments. [T3] Our reading is that this is the boundary that
distinguishes this case from every other in the library, because it is the only
one where the agent's own action produces an authoritative observation. A test
result is not an opinion about the edit; it is a fact about it.

**Instance to harness.** [T1] Instances are drawn from real issues and their
corresponding pull requests. [T3] Our reading is that the pairing is what makes
the boundary automatic: the criterion arrives with the task rather than being
authored separately, which is the property that makes 2,294 instances
maintainable.

## What this diagram does not show

Nearly everything about the agent, deliberately:

- **The tool set and interface design.** The paper's title claims the interface
  is decisive, and our material does not describe it. This is the single largest
  gap in the case.
- **The loop and its bounds.** Step count, retries, and stop condition are all
  unknown.
- **The context strategy.** A repository does not fit in a window, so there is
  one, and we cannot source it.
- **The resolution mechanism.** Our reading that tests supply the oracle is an
  inference, not a description, and it is flagged as such wherever it appears.
- **Cost and latency.** No figures exist in our material and none are estimated.
