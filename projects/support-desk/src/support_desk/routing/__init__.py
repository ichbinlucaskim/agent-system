"""Layer 2 — route FAQ (cheap) vs account (agent loop).

Purpose
    Decide whether a customer message is a read-only policy question or an
    account-changing request that needs tools, HITL, and budgets.

Why
    Routing is a separate layer so cost and risk stay aligned: FAQ pays for one
    retrieval + one completion; refunds and cancels enter the full agent path.
    Keeping the decision out of tools_gate and agent keeps each layer single-
    purpose.

Trade-offs
    Heuristic keyword / order-id matching is cheap and deterministic, but can
    mis-route ambiguous phrasing. False account routes cost more; false FAQ
    routes may answer without tools when a side effect was intended.

Edges
    Import ``routing.route.route`` for the classifier. Package init stays thin.
"""
