"""Layer 1 — tools, HITL, account DB, policy corpus, guardrails.

Permission and side effects live here. Written policy is retrieved for
reference; enforcement is in tool preconditions and policy_gate.

Import concrete modules (``tools_gate.tools``, ``tools_gate.policy_gate``,
...) rather than relying on package re-exports, to avoid import cycles.
"""
