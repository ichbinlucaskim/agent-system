# Open questions - 06 Tool-agent-user support agent

The whole case is reasoning from a premise, so the open questions here are
unusually fundamental. The first one is whether the case should exist in its
current form at all.

## Unknown mechanism

- **What does tau-bench actually measure?** We have its title, its authors, and
  its identifier, and we have deliberately not inferred anything further. This
  matters because the case is named after the benchmark's framing while
  containing none of its content, which is a slightly uncomfortable position for
  a library with this library's rules. Reading the paper would answer it and
  would likely replace half of the [T3] material here with sourced content.

- **How much of a written policy can be compiled into tool preconditions?**
  Dimension 5 poses this as the central design question of the archetype and
  does not answer it. It matters because it is the difference between a
  constraint that holds and a constraint that is requested. A worked example of
  a policy rendered as tool-layer checks, along with an account of what part
  resisted compilation, would answer it.

- **How is escalation to a human operator triggered?** Any real system of this
  shape has one, and we have no material on what triggers it, what the operator
  receives, or whether the agent can be overruled after acting. This matters
  because escalation is the actual recovery mechanism for dimension 9, where we
  currently say only that retry does not apply.

- **How is the user authenticated, and what does the agent do with an
  authentication that is weak?** Everything in dimension 3 about user statements
  being unreliable assumes the identity behind them is settled. It often is not.
  This is upstream of the archetype as we have drawn it and it changes the
  design.

- **What happens when the policy is ambiguous?** We treat the policy as
  authoritative and static, which makes it sound like a decision procedure.
  Written policies are prose and contain genuine ambiguity. Whether such cases
  are refused, escalated, or resolved by the model is unknown, and it is
  probably where most real failures live.

## Unknown magnitude

- **How often does the correct-message-wrong-action failure occur?** We name it
  as the defining failure of the archetype and have no measurement of its rate
  in any system. Without one we cannot say whether it is a dominant concern or a
  tail risk, and the case argues for a specific evaluation practice on the
  strength of it. Action-trace scoring on a real deployment would answer it.

- **What does the refusal-collapse drift look like over time?** We assert that
  optimizing measured helpfulness pushes systematically toward acting. That is a
  mechanism claim with no magnitude attached. Tracking refusal rate against a
  helpfulness metric across releases would answer it.

- **What latency budget do these systems actually run under?** Dimension 12 says
  interactive and gives no figure, because we have none.

## Disputed between sources

None, because there is only one source and it is used for three facts. The
absence of disagreement here reflects an absence of sources rather than a
consensus, and it should not be read as confidence.

## Deliberately out of scope

- **Whether a support agent should exist for a given policy domain.** That is a
  product and risk decision rather than an architecture question. Case
  `07-workflow-not-agent` holds the general form of the question.

- **Regulatory and compliance constraints on automated customer action.** Real,
  jurisdiction-specific, and outside what a design-teardown library can
  responsibly cover.

- **The design of the policy itself.** This library studies systems that operate
  under a policy. How to write a good one is a different discipline, and
  pretending otherwise would put unsourced opinion in a document that is already
  mostly reasoning.
