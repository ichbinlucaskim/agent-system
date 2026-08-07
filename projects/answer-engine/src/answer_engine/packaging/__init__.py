"""Packaging layer marker.

Purpose
    Hold config and CLI/HTTP adapters.

Why
    Import ``packaging.config`` / ``packaging.app`` directly to avoid cycles
    with ``pipeline``.

Trade-offs / Edges
    Empty re-exports by design.
"""
