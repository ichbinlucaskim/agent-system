"""Layer 1 — tools, HITL, account DB, policy corpus, and guardrails.

Purpose
    Own every side effect and permission decision: SQLite account state,
    business tool executors, policy-gate classification (auto / confirm /
    forbidden), retrieval of written policy as reference data, and input /
    untrusted-content guardrails.

Why
    Case 06's core lesson: written policy is not permission. Enforcement must
    live in tool preconditions and the policy gate, not in model prose or
    retrieved markdown. Isolating this layer makes that boundary obvious.

Trade-offs
    This package does not re-export symbols. Callers import concrete modules
    (``tools_gate.tools``, ``tools_gate.policy_gate``, …) to avoid import
    cycles with ``agent.loop`` and ``packaging``.

Edges
    Retrieved policy text is wrapped as untrusted data; it never authorizes
    refunds or cancels. Forbidden tools (e.g. ``wipe_account``) are refused
    before any executor runs.
"""
