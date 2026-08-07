"""Layer 3 — agent loop with budgets and stop reasons.

Purpose
    Host the FAQ completion path and the multi-step account tool loop, plus
    the shared ``handle_message`` entry used by CLI, HTTP, and eval.

Why
    Budgets, stop reasons, and message assembly are orchestration concerns—
    not tool policy and not packaging adapters. Isolating them makes lab 12
    (bounded agents) readable next to lab 14 (HITL) and lab 18 (packaging).

Trade-offs
    This layer imports packaging ``Config`` and tools_gate symbols; packaging
    must not import this package's ``__init__`` in a way that cycles. Prefer
    ``from support_desk.agent.loop import …``.

Edges
    Input guardrails and routing run in ``handle_message`` before either path.
"""
