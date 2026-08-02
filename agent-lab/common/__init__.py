"""Shared helpers used by every lab in this repository.

The modules here are deliberately small. They exist so that each lab can focus
on one idea instead of re-implementing client setup, tracing, cost accounting,
and vector storage.

Modules:
    client       Thin wrapper around the Anthropic SDK.
    tracing      Step-level trace records and a text report renderer.
    cost         Token accounting and a per-model price table.
    vectorstore  In-memory vector store with optional sqlite3 persistence.
"""

__all__ = ["client", "cost", "tracing", "vectorstore"]
