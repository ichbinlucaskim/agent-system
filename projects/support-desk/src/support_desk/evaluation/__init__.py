"""Layer 4 — action-level evaluation and run reports.

Purpose
    Score support-desk behavior on whether the right tools succeeded or were
    blocked, and render short cost/latency/audit reports from run traces.

Why
    Case 06 quality is about actions (refund issued, wipe forbidden), not
    fluent answers. Keeping eval in its own layer makes the suite the contract
    for tools_gate and agent changes.

Trade-offs
    Offline cases use scripted tool plans; they do not measure live model
    judgment. Observe reports are text for terminals, not structured metrics
    exporters.

Edges
    Import ``evaluation.runner`` and ``evaluation.observe`` directly.
"""
