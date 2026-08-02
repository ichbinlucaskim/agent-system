# Reading paths

Three routes through the seven topics. Pick the one that matches what you are
trying to build, and ignore the other two.

**These orderings are a study opinion, not a consensus.** They reflect how one
reader chose to arrange this particular set of sixteen papers. Nobody in the
field agreed on them, no survey backs them, and a different reader with a
different goal would order them differently and be equally justified. Treat
them as a starting sequence you are free to abandon.

## Default

```text
01-reasoning
  -> 02-acting-and-tools
    -> 03-self-correction
      -> 04-memory-and-retrieval
        -> 07-evaluation
          -> 05-multi-agent
            -> 06-environment-and-interface
```

Reasoning first, because everything else is built on a single call producing
intermediate steps. Then acting, which turns those steps into a loop. Then
self-correction, which is what you reach for once that loop produces a first
attempt worth improving. Then memory and retrieval, which is the answer to the
loop running out of context.

Evaluation comes before multi-agent deliberately. Once you can measure an
agent, claims about coordination have somewhere to land, and you can tell an
improvement from a rearrangement.

**Multi-agent comes late because the single-agent loop should be understood
first.** Almost every coordination problem between agents is a problem the
single-agent loop already has, and reading about orchestration before you have
felt a loop fail to terminate makes the multi-agent papers look like solutions
to problems you have not met.

Environment and interface comes last not because it is least important, but
because its central argument, that the action surface is a design variable,
lands hardest once you have already accepted every other interface in the
stack as fixed.

## RAG-focused

```text
04-memory-and-retrieval
  -> 02-acting-and-tools
    -> 07-evaluation
```

For building a retrieval system rather than an autonomous agent. Start with
retrieval as a component of generation, then read the acting papers for the
loop that lets a system decide to retrieve again rather than retrieving once
up front, then evaluation, because retrieval quality is the part of this stack
that is most often asserted and least often measured.

Skipping reasoning here is a deliberate trade. You will understand what the
retrieval system does without understanding why the generation step behaves as
it does, which is usually acceptable until it is not.

## Evaluation-focused

```text
07-evaluation
  -> 03-self-correction
    -> 02-acting-and-tools
```

For someone who has inherited an agent and has to find out whether it works.
Start with how these benchmarks are constructed and what that construction
makes measurable. Then self-correction, because an evaluator and a critic are
the same machinery pointed in different directions, and reading them together
makes the reuse obvious. Then acting, to understand the loop you are measuring.

This route reads the field backwards on purpose. It gets you to a number
sooner, at the cost of understanding later what the number is made of.

## What none of these cover

This library is sixteen papers. It has no coverage of pretraining, alignment
technique, inference optimization, or the model-internals literature. Those are
not omissions from the reading paths, they are omissions from the library, and
they are worth knowing about before you treat any of these routes as complete.
