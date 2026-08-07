"""Answer engine package — pure workflow worked example of system-design case 02.

Purpose
    Teach read-only answering where correctness is forced by grounding, not by
    a post-hoc verification agent or HITL.

Why
    Contrasts with ``projects/support-desk`` (case 06), which mixes workflow with
    a bounded agent loop on side-effecting tools.

Trade-offs
    Hash embeddings and lexical rerank copy the *shape* of commercial stacks,
    not their quality.

Edges
    See README pipeline diagram; abstain when evidence is weak.
"""

__version__ = "0.1.0"
