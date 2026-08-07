from answer_engine.retrieval import CorpusIndex, hybrid_retrieve, keyword_score


def test_corpus_loads():
    index = CorpusIndex.build()
    assert "grounding" in index.documents
    assert len(index.passages) >= len(index.documents)


def test_hybrid_prefers_grounding_for_evidence_query():
    index = CorpusIndex.build()
    hits = hybrid_retrieve(index, "fluent answer outruns its evidence", shortlist=5)
    docs = {h.doc_id for h in hits[:3]}
    assert "grounding" in docs


def test_keyword_score_overlap():
    assert keyword_score("hybrid retrieval", "hybrid retrieval combines keyword") > 0.5
