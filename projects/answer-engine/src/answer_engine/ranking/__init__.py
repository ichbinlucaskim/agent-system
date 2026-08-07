"""Staged reranking, quality threshold, and one retrieval restart.

Purpose
    Spend more compute on fewer candidates, then optionally restart when the
    candidate set is too weak.

Why
    Case 02 reconstructions agree on staged ranking and (in one source) a
    fail-safe that discards a weak set and retrieves again. Latency budgets are
    why the stack is staged at all.

Trade-offs
    Our "careful" stage is still lexical, not a cross-encoder. We copy the
    *shape* (cheap then careful then threshold), not a guessed commercial stack.

Edges
    Restart runs at most once. If still weak, callers may still receive the
    best available ranked list; abstain is decided later in ``pipeline``.
"""

from __future__ import annotations

from answer_engine.retrieval import (
    CorpusIndex,
    Passage,
    careful_score,
    hybrid_retrieve,
)


def stage_rerank(query: str, shortlist: list[Passage], *, keep: int = 5) -> list[Passage]:
    """Reorder a hybrid shortlist with careful_score.

    Purpose
        Promote passages that densely match content tokens.

    Why
        Must not invent new candidates: only permute the shortlist (lab 09).
        A doc the cheap pass missed can never be recovered here.

    Trade-offs
        keep truncates before threshold; too small keep starves the quality bar.

    Edges
        Empty shortlist returns []. Ties break on hybrid_score then id.
    """
    rescored: list[Passage] = []
    for passage in shortlist:
        rescored.append(
            Passage(
                id=passage.id,
                text=passage.text,
                doc_id=passage.doc_id,
                keyword_score=passage.keyword_score,
                vector_score=passage.vector_score,
                hybrid_score=passage.hybrid_score,
                careful_score=careful_score(query, passage.text),
            )
        )
    rescored.sort(key=lambda p: (-p.careful_score, -p.hybrid_score, p.id))
    return rescored[:keep]


def apply_quality_threshold(
    passages: list[Passage], *, min_score: float, min_keep: int = 1
) -> tuple[list[Passage], bool]:
    """Filter by score floor; report whether the set is too weak.

    Purpose
        Decide if fail-safe restart should fire.

    Why
        Case 02 fail-safe exists for "no clear candidates." ``weak=True`` is that
        signal without yet changing control flow.

    Trade-offs
        Using OR of careful/hybrid is permissive. AND would abstain more often.

    Edges
        min_keep=1 with empty kept => weak. Passages already truncated by caller.
    """
    kept = [p for p in passages if p.careful_score >= min_score or p.hybrid_score >= min_score]
    if len(kept) >= min_keep:
        return (kept, False)
    return (kept, True)


def rank_with_failsafe(
    index: CorpusIndex,
    query: str,
    *,
    shortlist: int = 12,
    keep: int = 3,
    min_score: float = 0.05,
    broadened_query: str | None = None,
) -> tuple[list[Passage], dict]:
    """Hybrid → rerank → threshold; optionally one broadened restart.

    Purpose
        Produce the final passage list for prompt assembly, plus a rank trace.

    Why
        Encodes the case 02 control-flow exception (restart) without becoming
        an agent loop: still a fixed graph with one optional back-edge.

    Trade-offs
        Restart lowers the threshold by half to avoid infinite weakness. That
        can admit noisier passages; ``pipeline`` still requires keyword_score>0.

    Edges
        If kept is empty after restart, falls back to top ``keep`` of ranked so
        the caller always gets a list (may then abstain upstream).
        broadened_query equal to query skips restart.
    """
    trace: dict = {"restarts": 0, "queries": [query]}
    candidates = hybrid_retrieve(index, query, shortlist=shortlist)
    ranked = stage_rerank(query, candidates, keep=max(keep, 5))
    kept, weak = apply_quality_threshold(ranked, min_score=min_score, min_keep=1)

    if weak and broadened_query and broadened_query != query:
        trace["restarts"] = 1
        trace["queries"].append(broadened_query)
        candidates = hybrid_retrieve(index, broadened_query, shortlist=shortlist)
        ranked = stage_rerank(broadened_query, candidates, keep=max(keep, 5))
        kept, weak = apply_quality_threshold(ranked, min_score=min_score * 0.5, min_keep=1)
        trace["weak_after_restart"] = weak

    final = kept[:keep] if kept else ranked[:keep]
    trace["passage_ids"] = [p.id for p in final]
    trace["scores"] = [
        {
            "id": p.id,
            "hybrid": round(p.hybrid_score, 4),
            "careful": round(p.careful_score, 4),
        }
        for p in final
    ]
    return (final, trace)
