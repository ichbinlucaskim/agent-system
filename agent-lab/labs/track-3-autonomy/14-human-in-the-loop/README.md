# Lab 14 - Human in the loop

## Goal

After this lab you can put a person in the path of an agent's actions: classify every action as automatic, needing confirmation, or forbidden; enforce that classification in code; and render a diff so the approver sees what will actually change.

## Prerequisites

Labs 01, 07, and 12. Concepts: the tool-use boundary, and reversibility as a way of ranking risk.

## Estimated time

45 to 60 minutes

## Background

The gap between a `tool_use` block and your code executing it is the only place a person can stand. Everything in this lab lives in that gap, which is why the tool boundary from lab 01 mattered.

Classify by reversibility and blast radius, not by how the tool sounds. Reading a file is automatic. Writing one is a confirmation, because it destroys the previous contents. Sending an email is a confirmation because you cannot unsend it. Deleting a production database is forbidden, meaning the agent is not given the capability at all.

Forbidden must be enforced in code. A system prompt saying never to do something is a request, and a request is exactly what a prompt injection is designed to overwrite. If an action must never happen, the tool must not exist in the agent's tool set, or the executor must refuse the name.

A confirmation prompt that shows only the tool name teaches people to click approve. What makes approval real is showing the consequence: the exact diff for a file write, the recipient and subject for an email, the row count for a delete. Approval fatigue is a design failure, not a user failure.

Auto-approve is a policy decision with a cost. Widening it makes the agent faster and moves risk onto whatever runs after it. Narrowing it makes the agent safer and, past some point, so slow that people route around it. Write the policy down, keep it in one place, and change it deliberately.

Log every decision, including the automatic ones. When something goes wrong, the question is always what was approved, by whom, and what it actually did, and that question can only be answered from a record written at the time.

## Steps

1. Write `POLICY`: a single mapping from tool name to `auto`, `confirm`, or `forbidden`, with a comment explaining the reversibility reasoning behind each entry.
2. Implement `classify_action`: return the policy class for an action, defaulting unknown tools to `confirm` rather than `auto`.
3. Implement `render_diff`: use `difflib` to show exactly what a write changes, including the path and the added and removed lines.
4. Implement `approve`: present the action, and for a write present the diff, then take a yes or no from an approver callback so it can be scripted in tests.
5. Implement `guarded_execute`: refuse forbidden actions before any prompt, run auto actions directly, and require approval for the rest. Return an audit record for every path.
6. Add a denial reason and pass it back to the model as a tool result, so a refused action becomes information rather than a dead end.

## Verification

```bash
pytest labs/track-3-autonomy/14-human-in-the-loop/tests -v
```

The policy layer is pure logic and is tested offline. Passing means a forbidden action never reaches the executor and never prompts anyone, an auto action runs without an approver, a confirm action calls the approver and is not executed when denied, the diff shows both added and removed lines, and every path returns an audit record.

## Going further

- Add a rule that escalates a normally automatic action to confirmation past a threshold, such as deleting more than ten files.
- Batch several pending actions into one approval and decide whether that reduces fatigue or hides detail.
- Have a denied action come back to the model with the reason, and see whether it proposes a safer alternative or simply retries.

## Certification mapping

- **Anthropic, Building Effective Agents and Effective context engineering for AI agents**: Human oversight at the agent-computer interface; designing for recoverable errors.
- **Databricks Generative AI Engineer Associate**: Governance; tool and agent frameworks.
- **NVIDIA NCA Generative AI LLMs**: Alignment; software development.

Exam objectives change over time. Treat this as a pointer, not a syllabus, and check the official exam guides directly. See `docs/cert-mapping.md` for the full table.
