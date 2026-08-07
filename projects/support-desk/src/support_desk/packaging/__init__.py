"""Layer 5 — config, CLI/HTTP adapters, smoke, and MCP stdio server.

Purpose
    Own process boundaries: environment config, argparse CLI, Threading HTTP
    server, health smoke, and a thin MCP-style order lookup server—without
    reimplementing agent logic.

Why
    Lab 18 packaging lesson: adapters stay thin over ``handle_message``. This
    layer is where ports, API keys, and transport live so tools_gate and agent
    remain transport-agnostic.

Trade-offs
    Package ``__init__`` stays empty of imports to avoid cycles with
    ``agent.loop`` (which imports ``packaging.config``). Callers import
    ``packaging.config``, ``packaging.app``, or ``packaging.mcp_order_server``
    directly.

Edges
    Live ``ask`` / ``serve`` require ``ANTHROPIC_API_KEY``; smoke can omit it.
"""
