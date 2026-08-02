# The twelve dimensions

Every case in this library is described along the same twelve dimensions. The
point of a fixed set is comparability: when two systems are written up against
the same questions, the places they differ are visible, and the places a
write-up is silent are visible too.

Each dimension below states the question it answers and why it discriminates
between designs. A dimension that did not discriminate would not earn a column
in `comparison.md`.

## 1. Problem and success criteria

**The question:** what counts as done, and who or what decides? This is the
first dimension because it constrains all the others. The sharpest distinction
it draws is whether a machine-checkable oracle exists. A system whose output
can be checked automatically can be built around a retry loop and evaluated by
running it. A system whose output can only be judged by a person has to spend
its design budget on making the output reviewable instead, and its evaluation
becomes a research problem rather than a test run.

## 2. Autonomy level

**The question:** are the steps laid out in code ahead of time, or does the
model decide what to do next? This is a spectrum rather than a binary, and
placing a case on it predicts most of its other properties: cost, latency,
debuggability, and the kind of failure you get when it goes wrong. Systems at
the predefined end fail in ways you can reproduce. Systems at the model-directed
end fail in ways you have to reconstruct from a trace.

## 3. Observation space

**The question:** what can the system see, and at what point in the loop does it
see it? Observation bounds everything downstream, because a system cannot
correct an effect it cannot observe. It also discriminates on cost, since
observation is usually the largest consumer of context. Two systems with
identical action spaces behave very differently when one can read the result of
its actions and the other cannot.

## 4. Action space

**The question:** what can the system change outside itself, and can the change
be undone? Read-only against mutating is the sharpest single line in this
library, and reversibility is the axis that decides how much permission
machinery is worth building. An action that can be undone with a keystroke
justifies almost no gating. An action that cannot be undone at all justifies
refusing to make the capability available, rather than asking about it.

## 5. Tools and agent-computer interface

**The question:** what surface does the model choose over, and how much of the
design lives in that surface rather than in the prompt? This dimension
discriminates between systems that treat the interface as given and systems
that treat it as the primary design variable. The distinction matters because
an interface constraint holds whatever the model decides, and a prompt
instruction does not.

## 6. Context strategy

**The question:** what occupies the context window at each step, and what
happens to material that no longer fits? This determines whether a system can
run long. Every design in this library that operates over more material than
one window can hold has an answer here, and the answers differ enough to be
diagnostic: summarizing, delegating to a fresh window, writing to storage, or
simply refusing to grow.

## 7. Memory and state

**The question:** what survives a single step, a session, and a full run? This
separates a system that can be resumed from one that has to start over, which
in turn decides whether long-running work is viable at all. It also exposes
where the durable record lives, which is usually where recovery and auditing
have to attach.

## 8. Control flow

**The question:** who decides the next step, and what bounds that decision? This
is the most predictive dimension for debuggability. When control flow lives in
code, a failure has a line number. When it lives in the model, a failure has a
transcript, and the work of understanding it is qualitatively different. The
bounds matter as much as the locus: an unbounded model-directed loop and a
step-limited one are different designs.

## 9. Error handling and recovery

**The question:** when a step fails, is the failure data the system reasons
about or an exception that ends the run? Systems that return errors into the
loop can adapt and can also spin. Systems that raise are easier to reason about
and give up sooner. The dimension discriminates because the same underlying
mechanism, a failed tool call, is treated as a normal event by some designs and
as a terminal one by others.

## 10. Human involvement and permissions

**The question:** where does a person stand relative to the system's actions,
and is that position enforced or requested? This decides whether a system can
run unattended, which is usually the difference between a demo and something
that operates. Requested involvement, meaning an instruction in a prompt, and
enforced involvement, meaning a check outside the model, look similar in a
transcript and behave differently under a model that decides otherwise.

## 11. Evaluation

**The question:** how do you know a change made things better? This is dimension
1 seen from the process side. It discriminates on what the evaluation costs to
run: a test suite is nearly free and can gate every change, while a human
review or a model-judged rubric is expensive enough that it runs on a schedule
and lags development. The lag is the design consequence.

## 12. Cost and latency budget

**The question:** what is this design allowed to spend per unit of work, in
tokens and in wall-clock time? Budget is a constraint that propagates upward
into architecture rather than a number tuned at the end. A hard interactive
latency budget forbids verification loops outright and forces correctness to be
handled some other way. A generous batch budget permits several passes over the
same work and makes verification affordable.
