# Architecture - 06 Tool-agent-user support agent

> This diagram is [T3] throughout. It draws the archetype as we describe it in
> `README.md`, not a real deployed system, and not anything attributed to
> tau-bench beyond the tool-agent-user framing its title states.

## Shape

```text
   +-------------+                      +-------------------------+
   |    user     |<-------------------->|         agent           |
   |             |   [T3] alternating   |                         |
   | statements  |        turns; the    |                         |
   | may be      |        user, not the |                         |
   | mistaken,   |        agent, ends   |                         |
   | incomplete, |        the exchange  |                         |
   | or strategic|                      |                         |
   +-------------+                      +-------------------------+
                                          |         |          ^
                     [T3] read-only,      |         |          |
                     authoritative,       |         |          |
                     static               |         |          |
                          +---------------+         |          |
                          |                         |          |
                          v                         v          |
                  +---------------+       +--------------------+---+
                  |    policy     |       |   tool layer           |
                  |   (document)  |       |   business operations  |
                  +---------------+       +------------------------+
                                                     |
                        [T3] the gap this archetype  |
                        turns on: the constraint     |
                        lives in the document, the   |
                        capability lives here        v
                                          +------------------------+
                                          |   account state        |
                                          |   [T3] authoritative,  |
                                          |   mutable, shared with |
                                          |   other actors         |
                                          +------------------------+
                                                     |
                                                     v
                                          +------------------------+
                                          |  side effects outside  |
                                          |  the system: money,    |
                                          |  scheduling, access    |
                                          |  [T3] consequence is   |
                                          |  not undone by undoing |
                                          |  the state change      |
                                          +------------------------+
```

## Flow

All [T3].

1. The user states a request. It is evidence about what they want and about what
   they believe they are entitled to, and it is not evidence about the policy.
2. The agent reads account state. This must be a fresh read rather than a recall
   from earlier in the conversation, because the agent's own prior actions may
   have changed it.
3. The agent decides whether the policy permits the action the request implies.
   In the naive construction this decision happens entirely inside the model,
   because the policy is prose in the context window.
4. If permitted, the agent calls a tool. The state changes and a consequence
   leaves the system.
5. The agent reports back. The report is the only artifact most evaluations
   examine, and it is produced after the irreversible part has already happened.
6. The user takes another turn, or does not. The agent does not control
   termination.

## Boundaries

All [T3].

**Policy to tool layer.** The boundary that does not exist, and the one the
archetype is about. The constraint is a document and the capability is an API,
so nothing structurally prevents a tool call the policy forbids. The design
question is how much of the policy can be moved across this boundary into
preconditions on the tools.

**Agent to side effects.** One-way. Everything to the right of the tool layer
leaves the system, which is what makes step 4 the point of no return and step 5
too late for correction.

**User to agent.** Two-way and, unusually for this library, adversarially
capable. The user is not hostile by default and is also not a neutral sensor.

## What this diagram does not show

- **Any real product.** No support agent's architecture is depicted here. The
  boxes are the archetype's minimum parts, not an observed implementation.
- **Anything from tau-bench beyond its framing.** The benchmark's tasks,
  domains, metrics, and user simulation are not in our material and are not
  drawn.
- **Escalation to a human operator.** Almost certainly a component of any real
  system of this shape, and we have no material on how it is triggered or what
  it receives. See `open-questions.md`.
- **Authentication.** Establishing that the user is who they claim is upstream
  of everything here and is not modeled.
- **Any figures.** No latency budget, cost, or accuracy number appears anywhere
  in this case.
