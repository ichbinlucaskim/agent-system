# Architecture - 07 Workflow, not agent

## Shape

The diagram is the point of the case: there is very little to draw, and that is
the argument.

```text
   input
     |
     v
  +------------+     +------------+     +------------+
  |  stage 1   | --> |  stage 2   | --> |  stage 3   | --> output
  |            |     |            |     |            |
  | LLM call   |     | code       |     | LLM call   |
  | + retrieval|     | validation |     |            |
  +------------+     +------------+     +------------+
     ^                    |
     |                    | on failure: ordinary error handling
     |                    v
     |               +------------+
     +-------------- |  retry or  |
        bounded by   |  raise     |
        code, not    +------------+
        by a model

  [T1] LLMs and tools orchestrated through predefined code paths
```

Contrast with the equivalent sketch of an agent, which is the same picture with
the arrows removed and replaced by a model deciding which box to enter next.

```text
                 +---------------------+
        input -->|   model decides     |<--+
                 |   the next step     |   |
                 +---------------------+   |
                    |    |    |    |       |
                    v    v    v    v       |
                  tool tool tool tool -----+

  [T1] agents are systems where LLMs dynamically direct their own
       processes and tool usage
```

[T3] Our reading: everything else in this library is a consequence of choosing
the second diagram, and the choice is usually made implicitly.

## Flow

1. [T3] Input arrives in a shape the pipeline expects, or is rejected at the
   boundary.
2. [T3] Each stage runs in a fixed order with a fixed contract. An LLM call is
   one kind of stage, not the organizing principle.
3. [T3] Validation between stages is ordinary code, and a failure raises or
   retries in the ordinary way.
4. [T3] The output is produced by the last stage. There is no step at which the
   system decides it is done, because the code already knew.

## Boundaries

**Between stages.** [T3] The interesting boundary in this architecture, and the
one that carries the testability advantage: each is a contract that can be
asserted on with fixtures, independently of the stages around it.

**Between the pipeline and the model.** [T3] The model is called by the
pipeline; it does not call the pipeline. This inversion, relative to every other
case in the library, is what removes the tool-selection problem, the permission
problem, and the non-termination problem in one move.

## What this diagram does not show

- **Any specific pipeline.** This is the archetype, and a real one would have
  domain-specific stages.
- **The branch count over time.** [T3] The ossification failure mode in
  `README.md` is a claim about how this diagram evolves, and a static diagram
  cannot show it. A version of this drawing after two years of edge cases is the
  honest comparison, and we have no example to draw.
- **Where the checklist runs.** The checklist in `README.md` is a process
  artifact rather than a component. It runs before this diagram exists, and it
  should run again whenever a stage grows a branch.
