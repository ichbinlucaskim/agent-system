# Architecture - 03 Orchestrator-worker research system

## Shape

```text
                        user query
                             |
                             v
        +------------------------------------------+
        |  LeadResearcher                          |
        |                                          |
        |  [T1] thinks through the approach        |
        |  [T1] saves plan to Memory               |
        |  [T1] decides whether more research      |
        |       is needed; can spawn another       |
        |       wave or refine strategy            |
        +------------------------------------------+
             |            |            |
             |            |            |     [T1] subagents operate in parallel
             v            v            v
        +---------+  +---------+  +---------+
        | subagent|  | subagent|  | subagent|   [T1] each has its OWN
        |         |  |         |  |         |        context window
        | search  |  | search  |  | search  |   [T1] search independently
        +---------+  +---------+  +---------+
             |            |            |
             |  [T1] return DISTILLED findings, not raw sources
             +------------+------------+
                          |
                          v
        +------------------------------------------+
        |  LeadResearcher (drafting)               |
        |  holds: plan + distilled findings        |
        |  does NOT hold: the source documents     |  [T3] our reading
        +------------------------------------------+
                          |
                          v
        +------------------------------------------+
        |  CitationAgent                           |
        |  [T1] processes the source documents AND |
        |       the research report to identify    |
        |       where citations belong             |
        +------------------------------------------+
                          |
                          v
                 attributed report
```

### The Memory boundary

```text
   LeadResearcher context window
   +--------------------------------------------+
   |  plan, findings, drafting state             |
   |                                             |
   |  [T1] if the context window exceeds         |
   |       200,000 tokens it will be truncated   |
   +--------------------------------------------+
                    |
                    | [T1] the plan is saved to Memory
                    v
   +--------------------------------------------+
   |  Memory                                     |
   |  [T1] persists context so the plan survives |
   +--------------------------------------------+
```

## Flow

1. [T1] The LeadResearcher thinks through the approach and saves its plan to
   Memory, so that the plan survives context window truncation.
2. [T1] It delegates specialized tasks to subagents operating in parallel.
3. [T1] Subagents search independently, each with its own context window.
4. [T1] Subagents return distilled findings.
5. [T1] The lead agent decides whether more research is needed, and can spawn
   another wave or refine strategy. Steps 2 through 5 therefore repeat an
   undetermined number of times.
6. [T3] Our reading: at drafting time the lead holds the plan and the distilled
   findings, and not the source documents its workers read.
7. [T1] A separate CitationAgent processes the source documents and the research
   report to identify where citations belong, so claims are attributed.

## Boundaries

**Worker to lead.** [T1] Distilled findings cross this boundary; raw sources do
not. This is the single most consequential boundary in the design. [T3] Our
reading is that it is what makes the system able to read an unbounded amount of
material, and simultaneously what creates the attribution problem that the
CitationAgent is built to solve.

**Lead to Memory.** [T1] The plan crosses this boundary specifically because the
context window is not durable past 200,000 tokens. [T3] Our reading is that this
is an admission that the working context is scratch space rather than storage.

**Report to CitationAgent.** [T1] Both the report and the source documents cross
into this component. [T3] Our reading is that this is the only place in the
architecture where drafted text and original sources are held together, which is
what makes attribution checkable at all.

## What this diagram does not show

- **How subtasks are specified.** [T1] tells us the lead delegates specialized
  tasks; the format of a task handed to a subagent is not described in our
  material. Unknown.
- **How findings are distilled.** [T1] says findings come back distilled. Whether
  the subagent summarizes on its own initiative, under instruction, or through a
  fixed output contract is not stated. Unknown, and it matters for anyone
  copying the pattern.
- **Where checkpointing attaches.** [T1] names checkpointing as a production
  concern without locating it. Unknown.
- **Wave count and termination.** [T1] says the lead can spawn another wave. No
  bound is described. Unknown.
- **Anything about latency.** The post as given to us reports a token multiple
  and an eval result, and no timing. Nothing is estimated here.
