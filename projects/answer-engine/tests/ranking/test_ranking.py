from answer_engine.ranking import rank_with_failsafe, stage_rerank
from answer_engine.retrieval import CorpusIndex, hybrid_retrieve


def test_rerank_is_permutation_of_shortlist():
    index = CorpusIndex.build()
    shortlist = hybrid_retrieve(index, "staged reranking latency", shortlist=8)
    ranked = stage_rerank("staged reranking latency", shortlist, keep=3)
    assert len(ranked) == 3
    assert {p.id for p in ranked} <= {p.id for p in shortlist}


def test_rank_returns_trace():
    index = CorpusIndex.build()
    passages, trace = rank_with_failsafe(
        index, "citations before generation", keep=3, min_score=0.01
    )
    assert passages
    assert "passage_ids" in trace
    assert trace["restarts"] in (0, 1)
