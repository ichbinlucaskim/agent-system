# 06 - Tool-agent-user support agent

## Representative system

None. This case is written as an archetype rather than as a study of a named
product.

[T1] The archetype takes its name and framing from tau-bench, arXiv 2406.12045,
Yao, Shinn, Razavi, Narasimhan: a benchmark for tool-agent-user interaction in
real-world domains.

> **What is sourced here and what is not.** The line above is the entire
> first-party content of this case: a title, an author list, and an
> identifier. Everything below is our own description of the archetype, marked
> [T3] throughout. Nothing here should be read as a claim about what that paper
> found, what it measures, or how any deployed support agent works. Where the
> other filled cases in this library describe systems, this one describes a
> shape, and it is included because the shape is missing from the rest of the
> library rather than because we have material on an instance of it.

## Why this archetype exists

This is the only case where the user is inside the loop rather than at the end
of it.

In case 01 a person supervises an agent working on their behalf. In case 03 a
person reads a report the system produced. In case 04 there is no person at all.
Here the person is a participant whose statements are inputs the agent acts on,
who does not know the policy the agent is bound by, and whose interests are not
automatically aligned with the operator's.

It is also the only case where the failure that matters is not a wrong answer.
[T3] Our framing: an agent acting on a customer's behalf under a written policy
fails in a way that has no analogue elsewhere in this library. It can produce a
completely accurate, well-written, helpful message and still have taken an
action it was not permitted to take. Every evaluation approach used in the other
cases scores the message.

## The twelve dimensions

All [T3]. This is our archetype description, reasoned from the framing of
tool-agent-user interaction under a written policy. None of it is attributed to
the paper beyond the framing itself.

### 1. Problem and success criteria

[T3] Resolve a customer's request by taking actions on their account, within a
written policy. Success has two parts that can come apart: the action must be
the one the customer needed, and it must be one the policy allows. A system
evaluated on only the first part will look excellent while being unusable, and a
system evaluated on only the second will be safe and useless.

[T3] This two-part criterion is the reason the case exists. Every other case in
the library has a single success axis.

### 2. Autonomy level

[T3] Agent, and necessarily so, because the path depends on what the user says
next and cannot be laid out in advance. The autonomy is bounded not by a step
budget, as in case 12's shape, but by a policy that constrains which actions are
available in which circumstances. That is a different kind of bound: it limits
what may be done rather than how long the doing may take.

### 3. Observation space

[T3] Three sources that differ in reliability, which is the interesting part.
The policy is authoritative and static. The account state is authoritative and
changes. The user's statements are neither: they may be mistaken, incomplete, or
strategic. An agent that treats all three as equally trustworthy inputs has a
design flaw rather than a prompting problem.

### 4. Action space

[T3] Mutating, with side effects that reach outside the system into money,
scheduling, and access. Technical reversibility is the wrong frame here: a
refund can be clawed back in a database and cannot be un-communicated to the
customer who was told it happened. The relevant question is not whether the
state can be restored but whether the consequence can be, and for most support
actions it cannot.

[T3] This is what separates the case from 01, where the action space is also
mutating. A bad file edit is undone by version control. A bad refund is a
business event.

### 5. Tools and agent-computer interface

[T3] Tools correspond to business operations, and the policy is not one of them.
This asymmetry is the design problem: the actions live in the tool layer where
they can be gated, and the constraint on them lives in a document that the model
reads. A policy expressed only as text in the context window is subject to
exactly the objection case 01 raises about prompt-expressed constraints, with a
higher price for being wrong.

[T3] The design question this case poses, and does not answer, is how much of a
written policy can be compiled into the tool layer as preconditions rather than
left as prose for the model to honor.

### 6. Context strategy

[T3] The policy has to be resident for the whole interaction, because any turn
might be the one where it applies. The conversation grows. The account state
needs to be current rather than remembered, since it can change between turns,
including as a result of the agent's own earlier actions.

### 7. Memory and state

[T3] Two distinct kinds, and conflating them is a failure mode. The conversation
is the agent's own state and can be summarized. The account is external state
the agent shares with other actors and must not cache, because a summary of an
account balance is a stale fact with consequences.

### 8. Control flow

[T3] Alternating and user-driven. The agent does not decide when the interaction
ends; the user does, or the policy does by making the request refusable. This is
the sharpest structural contrast with case 03, where the lead agent decides
whether to continue and nobody interrupts it.

### 9. Error handling and recovery

[T3] The category that has no equivalent elsewhere: an error may be an action
already taken. Recovery is not retry, because the failed step changed the world.
This pushes correctness upstream, toward refusing to take an action that cannot
be validated, since there is no downstream place to fix it.

### 10. Human involvement and permissions

[T3] The user is in the loop and is not the approver. This distinction is worth
stating plainly because case 01's permission model does not transfer: there, the
person being asked to approve an action is the person the agent works for. Here
the person in the conversation is the party the policy exists to adjudicate, and
asking them to approve an action on their own account is not an authorization
step.

[T3] Whatever approval exists has to come from the operator, ahead of time, in
the form of the policy and whatever the tool layer enforces. That is why this
case pushes toward compiled constraints rather than interactive gating.

### 11. Evaluation

[T3] Has to score the action trace against the policy, not the final message.
This follows directly from dimension 1, and it is the most transferable
observation in the case. A rubric applied to the transcript's last turn will
report success on a run whose middle contained a policy violation, and a run
that refused correctly will often read worse than one that helped incorrectly.

### 12. Cost and latency budget

[T3] Interactive, with a person waiting. That rules out the verification loops
case 04 can afford and pushes toward validity checks that are cheap enough to
run inline. It is a softer version of case 02's constraint: the budget is not as
tight as a search response, and it is nowhere near case 03's.

## Failure modes

All [T3], reasoned from the archetype rather than observed.

- **A correct message accompanying an incorrect action.** The transcript reads
  well and the side effect was wrong. This is the defining failure of the case,
  and it is invisible to any evaluation that scores text.
- **Treating a user statement as authorization.** A customer asserting they are
  entitled to something is evidence about their belief, not a fact about the
  policy. The failure is that these are the same kind of token in the context
  window.
- **Acting on stale account state.** A balance or status read earlier in the
  conversation and reused later, after the agent's own actions changed it.
- **Refusal collapse.** Because refusals read as unhelpful, pressure to improve
  measured helpfulness pushes systematically toward acting. The failure is a
  slow drift produced by the metric rather than a single bad decision.

## One thing to steal

Evaluate the action trace, not the final message.

[T3] Our reasoning: any agent whose actions have side effects has this exposure,
and the default evaluation shape, judging the output, is structurally blind to
it. The transferable practice is to record every action with its arguments and
score that sequence against the constraints separately from scoring the
response. It applies unchanged to case 01, and it is the one place where this
thinly-sourced case has something concrete to offer the well-sourced ones.

## One thing not to copy

Case 01's permission model, applied here without rethinking who the approver is.

[T3] Our reasoning: the interactive approval prompt is an excellent mechanism
when the person answering it is the principal the agent serves. In this
archetype the person in the conversation is the counterparty to the policy.
Wiring a confirmation step to them produces the appearance of a control and the
substance of none, and it is a mistake made easy by how well the pattern works
in case 01.

## Related

**Lab exercises:** `14-human-in-the-loop`, `07-tool-design-aci`,
`15-evaluation`, `12-agent-loop`.

**Paper topics:** `07-evaluation`, `02-acting-and-tools`.

**Other cases:** `01-terminal-coding-agent` for the permission machinery this
case cannot reuse directly, and `07-workflow-not-agent` for the question of
whether a constrained support flow needs an agent at all.
