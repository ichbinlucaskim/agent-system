# Sources - 06 Tool-agent-user support agent

This case has the weakest evidence base in the library, by construction. It is
included as an archetype because the shape is absent elsewhere, and the write-up
is honest about being reasoning rather than reporting.

## Tier definitions as used in this library

- **T1 first-party**: official documentation, the vendor's own engineering
  writing, papers by the system's authors, or public source code.
- **T2 second-party**: credible outside analysis or reverse engineering.
- **T3 inference**: our own reasoning, always phrased as our reading.

## T1

**tau-bench, arXiv 2406.12045.** Yao, Shinn, Razavi, Narasimhan. A benchmark for
tool-agent-user interaction in real-world domains.

This backs exactly three things and nothing else:

1. That the tool-agent-user interaction shape is a recognized object of study
   with a benchmark addressing it.
2. The name this case uses for the archetype.
3. The framing that the interaction involves a tool, an agent, and a user, taken
   from the title.

**Deliberately not attributed to this source:** what the benchmark measures, how
it constructs tasks, which domains it covers, how it simulates a user, what
metrics it reports, or any result. None of that is in our material. A reader who
wants those things should read the paper rather than this file.

## T2

None.

## T3

Everything else in this case folder. The twelve dimensions, the architecture
diagram, all four failure modes, the thing to steal, and the thing not to copy
are our own archetype reasoning.

The reasoning starts from one premise: an agent acts on a customer's behalf
under a written policy, the failure that matters is a policy-violating action
with a real side effect rather than a wrong answer, and the user is a
participant in the loop rather than a consumer of output. Each dimension is what
we think follows from that premise. The load-bearing steps are:

- **The two-part success criterion** (dimension 1), from which dimension 11
  follows directly. If correctness and permission are separate axes, then an
  evaluation reading only the final message can only see one of them.
- **Three observation sources of differing reliability** (dimension 3). Reasoning
  from the user being a participant with their own interests, which makes their
  statements evidence about belief rather than about entitlement.
- **Consequence rather than state as the unit of reversibility** (dimension 4).
  Reasoning from side effects that leave the system.
- **The policy-in-prose versus capability-in-tools asymmetry** (dimension 5).
  Reasoning by analogy from case 01's T1-sourced finding that prompt-expressed
  constraints do not survive a model that decides otherwise. The analogy is
  ours; case 01's underlying fact is first-party.
- **The user is not the approver** (dimension 10, and the thing not to copy).
  Reasoning from the user being the counterparty the policy adjudicates.

A reader who disagrees with the premise should discard the whole case, which is
the appropriate response to a document built this way.

## Deliberately excluded

- **Any named support product.** Naming one would require sourced material about
  it, and we have none. The `Representative system` heading says "none" rather
  than picking a plausible example.
- **Any characterization of tau-bench's contents or findings.** The temptation
  here is significant, because a benchmark title implies a great deal about what
  its authors considered important, and implication is not a source.
- **Any figure.** No accuracy, latency, cost, or task count appears in this case.
- **Escalation and authentication mechanics.** Real systems of this shape have
  both. We have no material, so they are open questions rather than boxes.
