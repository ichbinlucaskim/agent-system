"""Support desk: layered worked example of system-design case 06.

Purpose
    Expose the package version and document the five-layer layout that mirrors
    the case study: tools_gate → routing → agent → evaluation → packaging.

Why
    Case 06 teaches that permission, routing, budgets, eval, and adapters are
    separate concerns. Matching the package tree to those layers makes the
    teaching points discoverable in code, not only in prose.

Trade-offs
    Layers import downward (packaging → agent → tools_gate). Package ``__init__``
    files stay thin to avoid import cycles between agent and packaging.

Edges
    Import concrete submodules (e.g. ``support_desk.agent.loop``) rather than
    relying on re-exports from this root.
"""

__version__ = "0.1.0"
