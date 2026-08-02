# Open questions - 01 Terminal coding agent

This case has three fully sourced dimensions and two that are empty. The gaps
below are the reason.

## Unknown mechanism

- **What is the completion criterion?** Nothing in our material says how the
  system decides a task is done, or whether it decides at all rather than
  handing back to the user. This matters because dimension 1 constrains every
  other dimension, and our answer there is currently an inference we flagged as
  the weakest in the case. Documentation of the stop condition, or a transcript
  showing what ends a turn, would answer it.

- **What happens when a tool call fails?** Dimension 9 is empty. We do not know
  whether an error is returned into the model's context as an observation, or
  raised as a terminal condition, or retried. This matters because it decides
  whether the agent can adapt around a broken build command or stalls on it, and
  because it changes what a step budget actually bounds. The tool result schema,
  or documentation of retry behavior, would answer it.

- **What does the `memory` frontmatter field do?** We can source that it exists
  and nothing else. This matters because dimension 7 is the difference between a
  session that can be resumed and one that restarts, and because a memory that
  persists across sessions has a different security profile from one that does
  not. Field documentation would answer it.

- **In what order are deny rules and hooks evaluated relative to each other?**
  Both are documented as preceding the permission mode check, which is enough
  for the central claim of this case, but not enough to draw the pipeline
  precisely. This matters for anyone implementing a similar layered check, since
  a hook that can override a deny rule is a very different design from one that
  cannot. A statement of the full ordering would answer it.

- **What is the built-in tool inventory?** We can source how tools are
  configured and restricted but not what they are. This matters because
  dimensions 3 and 4 are descriptions of a tool set we cannot see, and both are
  currently written around a permission carve-out instead. The tool reference
  would answer it.

- **What does `isolation` isolate?** The field is sourced; its semantics are
  not. This matters because isolation is the mechanism that would let a
  permissive subagent be run safely, which bears directly on the "one thing not
  to copy" in this case. Field documentation would answer it.

## Unknown magnitude

- **What does always-on context actually cost?** Dimension 6 argues that
  material in `CLAUDE.md` is paid for on every turn, and we have no figure for
  what that costs in tokens or in latency, so `README.md` gives none. This
  matters because the guidance to move procedures into skills is a cost
  argument, and without a magnitude a reader cannot judge how much it is worth
  reorganizing for. Token accounting for a session with and without a large
  `CLAUDE.md` would answer it.

- **How many subagents can be registered before the selection surface degrades?**
  Names, descriptions, and tool lists load at session start, so the surface has
  a cost that grows with the number of subagents, and there is presumably a
  point where the model chooses worse among more options. We have no figure and
  do not guess one. A selection-accuracy measurement across registry sizes,
  which is close to what lab exercise `07-tool-design-aci` builds, would answer
  it.

## Disputed between sources

None. This case uses first-party documentation only, and the three sources do
not conflict on anything we drew from them.

## Deliberately out of scope

- **How Claude Code compares to other terminal coding agents.** A comparison
  needs sourced material on both sides, and we have it on one. It belongs in a
  separate case with its own sources rather than as an aside here.

- **Whether the seven customization surfaces are the right decomposition.** This
  is a design opinion about someone else's product rather than a question about
  what it does. The place for our view on surface count is the "one thing not to
  copy" section, where it is already marked as ours.

- **How the underlying model decides to call a subagent.** That is a question
  about model behavior rather than system architecture. It belongs with the
  paper topics `02-acting-and-tools` and `01-reasoning` in the sibling paper
  repository.
