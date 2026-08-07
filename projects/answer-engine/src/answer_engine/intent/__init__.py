"""Intent layer package.

Purpose
    Expose ``parse_intent`` and ``retrieval_query`` as the workflow's first stage.

Why / Trade-offs / Edges
    See ``intent.parse`` module docstring.
"""

from answer_engine.intent.parse import parse_intent, retrieval_query

__all__ = ["parse_intent", "retrieval_query"]
