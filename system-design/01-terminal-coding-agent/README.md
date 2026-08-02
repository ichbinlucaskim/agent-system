# 01 - Terminal coding agent

## Representative system

Claude Code.

## Why this archetype exists

This is the only case in the library where the agent mutates a filesystem the
user cares about, on the user's own machine, with no oracle to check the result
and no general undo. Case 04 also edits code, but inside a sandbox with a test
suite that says whether the edit was correct. Case 02 cannot change anything at
all. Case 03 produces a document.

What this case stresses, and nothing else here does, is **permission
architecture**: the machinery that decides which actions happen without asking,
which prompt first, and which are refused outright. In every other case that
question is either trivial because the action space is read-only, or deferred
because a sandbox absorbs the damage. Here it is the design.

## The twelve dimensions

### 1. Problem and success criteria

The work is project-situated rather than self-contained. [T1] The official
guidance describes `CLAUDE.md` as the place for facts the model should hold all
the time, naming build commands, monorepo layout, and team conventions as
examples, which locates the task inside an existing codebase with its own
conventions.

Our source material does not define a completion criterion. [T3] Our reading is
that there is no oracle in the general case, and that the developer reviewing
the resulting diff is the judge. This is the assumption the rest of the design
appears to be built around, but we cannot source it, and it is the first entry
in `open-questions.md`.

### 2. Autonomy level

Autonomy is a runtime setting here rather than a fixed property. [T1] Plan mode
prevents tool execution entirely, so the model can analyze and plan but cannot
make changes. [T1] At the other end, `bypassPermissions` skips permission
prompts. [T1] A `permissionMode` field in subagent frontmatter selects among
these per subagent.

[T3] Our reading is that this is one system spanning most of the workflow-agent
spectrum by configuration, which makes "how autonomous is it" the wrong question
to ask of the product and the right question to ask of a particular invocation.

### 3. Observation space

[T1] A subagent's `tools` and `disallowedTools` frontmatter fields configure
which tools it has, and `mcpServers` connects it to MCP servers, so the
observation space is defined per subagent by configuration.

Our source material does not enumerate the built-in tool inventory, so we cannot
state what the default observation space contains. [T3] The existence of a
documented carve-out for root and home directory removals implies the tool set
reaches the filesystem broadly enough for that carve-out to be necessary, but
that is an inference from a permission rule and not a description of the tools.

### 4. Action space

The action space includes filesystem mutation, and the strongest evidence in our
material is a permission rule rather than a tool description. [T1] Even under
`bypassPermissions`, root and home directory removals still prompt.

[T3] Our reading is that this carve-out is a statement about reversibility: the
design treats a small set of actions as never automatically approvable, no
matter how permissive the configured mode, because they cannot be undone. That
is a different mechanism from asking about an action, and it is applied to a
deliberately narrow set.

[T1] Three other categories also survive `bypassPermissions`: explicit ask
rules, connector tools an organization has set to ask, and MCP tools marked
`requiresUserInteraction`.

### 5. Tools and agent-computer interface

[T1] The documented customization surface is seven mechanisms: `CLAUDE.md` for
always-on project context, rules for hard constraints, skills for reusable
procedures, subagents for delegated work, hooks for deterministic automation,
output styles, and plugins to bundle the rest.

The subagent interface is the part with the most detail available. [T1]
Subagents are Markdown files with YAML frontmatter, stored in `.claude/agents/`
for project scope or `~/.claude/agents/` for user scope. [T1] The frontmatter
fields include `description`, `prompt`, `tools`, `disallowedTools`, `model`,
`permissionMode`, `mcpServers`, `hooks`, `maxTurns`, `skills`, `initialPrompt`,
`memory`, `effort`, `background`, and `isolation`. [T1] A subagent's name,
description, and tool list load at session start, but the body does not
auto-invoke; Claude calls a subagent through the Agent tool, passing a prompt
string.

[T3] Our reading is that this splits the subagent into a selection surface and
an execution surface. The name, description, and tool list are what the model
chooses over and are paid for in context on every session. The body is what runs
after the choice and costs nothing until invoked. That split is the reason a
subagent's description is a design artifact rather than documentation.

### 6. Context strategy

[T1] The guidance separates two kinds of material explicitly: `CLAUDE.md` is for
facts the model should hold all the time, and procedures belong in skills
instead. [T1] Subagent bodies are not loaded at session start.

[T3] Our reading is that these combine into three tiers: always resident
(`CLAUDE.md`), resident as a name and description but loaded on use (skills and
subagent bodies), and delegated into a separate context entirely (a subagent
run). The guidance to keep procedures out of `CLAUDE.md` is a rule about which
tier something belongs in, and the cost of getting it wrong is paid on every
turn of every session.

### 7. Memory and state

[T1] A `memory` field exists in subagent frontmatter. Our source material does
not describe its semantics, scope, or lifetime, so we do not describe them
either. See `open-questions.md`.

### 8. Control flow

Control is model-directed, with two documented mechanisms that move parts of it
back into code. [T1] Claude decides to call a subagent and does so through the
Agent tool, passing a prompt string. [T1] A `maxTurns` field bounds a subagent.
[T1] Hooks exist for deterministic automation.

[T3] Our reading is that hooks are the seam where a designer takes control flow
back from the model, and that the interesting question for any given behavior is
which side of that seam it should live on.

### 9. Error handling and recovery

Our source material says nothing about what happens when a tool call fails,
whether errors return into the loop, or whether a session can be resumed after a
crash. We are not going to reason our way to an answer that would read as
documentation. See `open-questions.md`.

### 10. Human involvement and permissions

This is the dimension the case exists for, and it is the best-sourced.

[T1] Permission checks run in order. Deny rules are checked first and block a
tool even in `bypassPermissions` mode. [T1] Hooks are evaluated before the mode
check and can still block a tool. [T1] The active permission mode is applied
after.

[T1] `bypassPermissions` skips permission prompts, with the four exceptions
listed under dimension 4. [T1] If the parent session uses `bypassPermissions` or
`acceptEdits`, that takes precedence and a subagent cannot override it.

[T3] Our reading, and the analytical point of this case: the same behavior can
be requested in a prompt or enforced in a hook, and only one of those two
survives a model that decides otherwise. Permission architecture, not prompt
wording, is what makes a filesystem-mutating agent safe to run unattended. The
ordering above is the concrete form of that claim, because it places two
mechanisms that live outside the model, deny rules and hooks, ahead of the mode
that the configuration selected.

[T3] A second reading of the precedence rule: because a permissive parent cannot
be tightened by a child, permission is a ceiling set at the top of a session
rather than a property negotiated per delegated task. A subagent's
`permissionMode` can only restrict within what the parent already allows.

### 11. Evaluation

Our source material contains nothing about how this system is evaluated. See
`open-questions.md`.

### 12. Cost and latency budget

[T1] Frontmatter exposes `model`, `effort`, `background`, and `isolation` as
per-subagent fields, which are the shape of a cost and latency control surface.

Our source material contains no figures of any kind: no token counts, no
latency, no pricing. We are not going to supply any. What can be said is
structural: [T3] the presence of per-subagent model and effort selection implies
that cost is expected to be tuned per delegated task rather than per session.

## Failure modes

All of the following are [T3], reasoned from the T1 facts above rather than
observed or reported. None of them is an incident report.

- **A permissive parent silently widens every child.** [T1] establishes that a
  parent's `bypassPermissions` or `acceptEdits` takes precedence and cannot be
  overridden by a subagent. A subagent authored with a careful restrictive
  `permissionMode` therefore provides no protection when invoked from a session
  that was started permissively. The subagent file looks safe when read in
  isolation, which is what makes this worth naming.
- **A constraint written in the wrong place stops holding.** A behavior
  expressed as prompt wording is advisory. The same behavior expressed as a deny
  rule or a hook is enforced, per the ordering in dimension 10. Both look
  identical in a passing transcript, and they diverge exactly when it matters.
- **The selection surface starves.** [T1] establishes that only a subagent's
  name, description, and tool list load at session start, and that the body does
  not auto-invoke. A subagent whose description does not say when to call it can
  therefore be perfectly written and never run, and the failure is silent.
- **Always-on context grows without a forcing function.** [T1] guidance puts
  procedures in skills rather than `CLAUDE.md`. Nothing in the mechanism
  prevents procedures accumulating in `CLAUDE.md` anyway, and the cost is paid
  on every turn of every session rather than at the moment of the mistake.

## One thing to steal

The check ordering. [T1] Deny rules are evaluated first and hold even in the
most permissive mode, and hooks are evaluated before the mode check. The
transferable idea is not the specific modes but the principle that the
enforcement layer sits outside the model and ahead of the configuration, so that
neither a model decision nor a permissive setting can reach past it. Any agent
with a mutating action space needs some version of this, and building it after
the fact is much harder than building it first.

## One thing not to copy

`bypassPermissions` as an operating default. It exists [T1] and it has carefully
chosen carve-outs [T1], and it is still a mode that answers "should I ask" with
"no" for everything else. [T3] Our reading is that it is defensible when the
action space has been narrowed by other means, such as a container or a
restricted tool list, and that copying the mode without also copying that
narrowing takes the convenience while leaving the safety behind.

Also worth resisting: adopting all seven customization surfaces because they
exist. [T3] Each one is a place a future reader has to look to understand why
the agent did something, and a project that needs two of them is better served
by using two.

## Related

**Lab exercises:** `07-tool-design-aci`, `13-subagents`, `14-human-in-the-loop`,
`12-agent-loop`, `11-context-memory`, `01-augmented-llm`.

**Paper topics:** `02-acting-and-tools`, `06-environment-and-interface`.

**Other cases:** contrast with `04-repo-scale-swe-agent`, which mutates code
under a test oracle, and with `02-answer-engine`, which cannot mutate anything.
