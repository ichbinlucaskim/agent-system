# Architecture - 01 Terminal coding agent

## Shape

Two structures are documented well enough to draw: the permission pipeline a
tool call passes through, and the split between a subagent's selection surface
and its execution surface.

### Permission pipeline

```text
        model requests a tool call
                  |
                  v
   +------------------------------+
   |  deny rules                  |  [T1] checked first; block even in
   |                              |       bypassPermissions mode
   +------------------------------+
                  |
   +------------------------------+
   |  hooks                       |  [T1] evaluated before the mode check;
   |                              |       can still block a tool
   +------------------------------+
                  |
                  v
   +------------------------------+
   |  active permission mode      |  [T1] applied after the above
   |    plan: no tool execution   |  [T1]
   |    acceptEdits               |  [T1] named in the precedence rule
   |    bypassPermissions         |  [T1] skips prompts, with carve-outs
   +------------------------------+
                  |
                  v
   +------------------------------+
   |  carve-outs that prompt even |  [T1] explicit ask rules
   |  under bypassPermissions     |  [T1] connector tools an org set to ask
   |                              |  [T1] MCP tools marked
   |                              |       requiresUserInteraction
   |                              |  [T1] root and home directory removals
   +------------------------------+
                  |
                  v
            tool executes
```

The vertical order of `deny rules` and `hooks` in this diagram is **not** a
claim. [T1] tells us deny rules are checked first and that hooks precede the
mode check, which fixes both of them ahead of the mode but does not fix them
relative to each other. See `open-questions.md`.

### Subagent selection and execution

```text
  session start
      |
      | [T1] loads: name, description, tool list
      |      does NOT load: body
      v
  +---------------------------+
  |  subagent registry        |     .claude/agents/    [T1] project scope
  |  (names + descriptions    |     ~/.claude/agents/  [T1] user scope
  |   + tool lists)           |     Markdown + YAML frontmatter [T1]
  +---------------------------+
      |
      | [T1] Claude calls a subagent through the Agent tool,
      |      passing a prompt string
      v
  +---------------------------+
  |  subagent run             |
  |  body + frontmatter apply |  [T1] tools, disallowedTools, model,
  |                           |       permissionMode, mcpServers, hooks,
  |                           |       maxTurns, skills, initialPrompt,
  |                           |       memory, effort, background, isolation
  +---------------------------+
      |
      | [T1] parent bypassPermissions or acceptEdits takes precedence;
      |      the subagent cannot override it
      v
  back to the parent session
```

## Flow

1. [T1] At session start, the names, descriptions, and tool lists of available
   subagents are loaded. Bodies are not.
2. [T3] Our reading: the model's choice of subagent is therefore made against
   the description alone, which is why the description carries design weight.
3. [T1] The model calls a subagent through the Agent tool, passing a prompt
   string. There is no documented mechanism for a subagent body to invoke
   itself.
4. [T1] The subagent's frontmatter configures its run, subject to the parent
   precedence rule.
5. [T1] Each tool call inside the run passes the permission pipeline above.

## Boundaries

The two boundaries that carry the design are both in the diagrams above.

**Model to enforcement.** [T1] Deny rules and hooks sit outside the model and
ahead of the configured mode. [T3] Our reading is that this is the only boundary
in the system that a model decision cannot cross, which is what makes it the
place to put a constraint that must hold.

**Parent to subagent.** [T1] Permission flows down and cannot be tightened by
the child. [T3] Our reading is that this makes the session start, not the
subagent file, the place where the safety envelope is actually set.

## What this diagram does not show

- The built-in tool inventory. Our source material configures tools
  (`tools`, `disallowedTools`) without enumerating them, so no tool boxes are
  drawn. Unknown, not unimportant.
- What happens on tool failure. Nothing in our material describes it. Unknown.
- Where `memory` lives or how long it survives. The field exists [T1]; the
  mechanism is undocumented in our material. Unknown.
- Anything about latency or token cost. No figures exist in our material and
  none are estimated here.
