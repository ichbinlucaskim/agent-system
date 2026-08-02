# Sources - 01 Terminal coding agent

Every tier tag in this case folder resolves to an entry here.

## Tier definitions as used in this library

- **T1 first-party**: official documentation, the vendor's own engineering
  writing, papers by the system's authors, or public source code.
- **T2 second-party**: credible outside analysis or reverse engineering.
- **T3 inference**: our own reasoning from a T1 or T2 fact, always phrased as
  our reading.

## T1

**Anthropic official documentation, `code.claude.com/docs/en/sub-agents`.**
Backs every claim in this case about subagent structure and permission
interaction:

- Subagents are Markdown files with YAML frontmatter, stored in
  `.claude/agents/` for project scope or `~/.claude/agents/` for user scope.
- Frontmatter fields include `description`, `prompt`, `tools`,
  `disallowedTools`, `model`, `permissionMode`, `mcpServers`, `hooks`,
  `maxTurns`, `skills`, `initialPrompt`, `memory`, `effort`, `background`,
  `isolation`.
- `bypassPermissions` skips permission prompts. Explicit ask rules, connector
  tools an organization set to ask, MCP tools marked `requiresUserInteraction`,
  and root and home directory removals still prompt.
- If the parent session uses `bypassPermissions` or `acceptEdits`, that takes
  precedence and a subagent cannot override it.

**Anthropic official documentation,
`platform.claude.com/docs/en/agent-sdk/permissions`.** Backs the permission
ordering in dimension 10 and the pipeline diagram:

- Permission checks run in order. Deny rules are checked first and block a tool
  even in `bypassPermissions` mode. The active permission mode is applied after.
- Plan mode prevents tool execution entirely. Claude can analyze and plan but
  cannot make changes.
- Hooks are evaluated before the mode check and can still block a tool.

**Anthropic,
`claude.com/blog/steering-claude-code-skills-hooks-rules-subagents-and-more`.**
Backs the customization surface list and the context tiering in dimension 6:

- Seven customization surfaces: `CLAUDE.md` for always-on project context, rules
  for hard constraints, skills for reusable procedures, subagents for delegated
  work, hooks for deterministic automation, output styles, and plugins to bundle
  the rest.
- `CLAUDE.md` is for facts Claude should hold all the time, such as build
  commands, monorepo layout, and team conventions. Procedures belong in skills.
- A subagent's name, description, and tool list load at session start, but the
  body does not auto-invoke. Claude calls a subagent through the Agent tool,
  passing a prompt string.

## T2

None. No second-party analysis was used for this case. Every factual claim here
is either first-party or explicitly marked as our inference.

## T3

Our inferences, each with the sourced fact it reasons from, so a reader can
check the step rather than the conclusion.

- **There is no oracle and the developer judges the diff** (dimension 1).
  Reasoning from the absence of any completion criterion in the T1 material,
  combined with the presence of review-oriented permission modes. This is the
  weakest inference in the case and is listed first in `open-questions.md`.
- **Autonomy is a runtime setting spanning most of the spectrum** (dimension 2).
  Reasoning from plan mode preventing execution entirely and
  `bypassPermissions` skipping prompts, both T1, being selectable through one
  `permissionMode` field.
- **The tool set reaches the filesystem broadly** (dimension 3). Reasoning from
  the existence of a root and home directory removal carve-out, T1. An inference
  from a permission rule, not a tool description.
- **The removal carve-out is a statement about reversibility** (dimension 4).
  Reasoning from that carve-out surviving the most permissive mode, T1, while
  ordinary prompting does not.
- **A subagent has a selection surface and an execution surface** (dimensions 5
  and 6). Reasoning from the T1 fact that name, description, and tool list load
  at session start while the body does not.
- **Context has three tiers** (dimension 6). Reasoning from the T1 separation of
  `CLAUDE.md` facts from skills procedures, plus deferred subagent body loading.
- **Hooks are the seam where control returns to code** (dimension 8). Reasoning
  from hooks being described as deterministic automation, T1, and evaluated
  ahead of the mode check, T1.
- **Permission architecture rather than prompt wording is what makes an
  unattended filesystem agent safe** (dimension 10). Reasoning from the check
  ordering, T1, which places two out-of-model mechanisms ahead of the configured
  mode. This is the central analytical claim of the case and it is ours, not
  Anthropic's.
- **Permission is a session-level ceiling** (dimension 10). Reasoning from the
  parent precedence rule, T1.
- **Cost is meant to be tuned per delegated task** (dimension 12). Reasoning
  from `model`, `effort`, `background`, and `isolation` being per-subagent
  frontmatter fields, T1.
- **All four failure modes.** Each names its T1 basis inline in `README.md`.
  None is an observed or reported incident.

## Deliberately excluded

- **The built-in tool inventory.** Convenient for dimension 3 and not present in
  our material. Left as an open question rather than assembled from memory.
- **Error handling and recovery behavior.** Dimension 9 is left empty for this
  reason. It would have been easy to write something plausible about tool errors
  returning into the loop, and there is no source for it here.
- **How the system is evaluated.** Dimension 11 is left empty for the same
  reason.
- **`memory` semantics.** The field name is sourced; everything about what it
  does is not.
- **Every quantity.** No token counts, latency figures, pricing, context window
  sizes, or version strings appear in this case, because none appear in our
  source material.
- **The relative order of deny rules and hooks.** Both are sourced as preceding
  the mode check. Their order with respect to each other is not, so the diagram
  declines to assert one.
