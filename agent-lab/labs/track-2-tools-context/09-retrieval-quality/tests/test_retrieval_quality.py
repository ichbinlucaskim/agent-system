"""Tests for Lab 09 - Retrieval quality.

Every metric and strategy in this lab is deterministic: the embedding is a
local hash stub and the scoring is plain arithmetic, so everything is tested
offline and no test needs an API key.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


def _load(name: str, path: Path):
    """Load a module by file path.

    The module is registered in sys.modules before execution because
    dataclasses look their own module up by name while being created.
    """
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


LAB_ROOT = Path(__file__).resolve().parents[1]
solution = _load("lab09_solution", LAB_ROOT / "solution" / "main.py")


def test_recall_at_k_matches_a_hand_counted_example():
    """Two relevant ids with one of them in the top 3 is recall 0.5."""
    retrieved = ["a", "b", "c", "d"]
    relevant = ["a", "z"]
    assert solution.recall_at_k(retrieved, relevant, k=3) == 0.5


def test_recall_at_k_only_considers_the_first_k():
    """A relevant id at position k+1 does not count."""
    retrieved = ["a", "b", "c", "target"]
    assert solution.recall_at_k(retrieved, ["target"], k=3) == 0.0
    assert solution.recall_at_k(retrieved, ["target"], k=4) == 1.0


def test_recall_at_k_handles_an_empty_relevant_list():
    """No relevant ids returns the documented 0.0 instead of dividing by zero."""
    assert solution.recall_at_k(["a", "b"], [], k=3) == 0.0


def test_sweep_returns_one_entry_per_chunk_size():
    """The sweep result has exactly the requested sizes as keys."""
    sizes = [120, 200, 400]
    results = solution.sweep_chunk_sizes(
        solution.CORPUS, solution.LABELLED_QUERIES, sizes, k=3
    )
    assert list(results) == sizes
    assert all(0.0 <= recall <= 1.0 for recall in results.values())


def test_every_sweep_size_chunks_the_corpus_differently():
    """No two sweep sizes are the same experiment run twice.

    Documents short enough to fit in one chunk produce identical stores at
    every size above their length, so the sweep reports a flat line that
    looks like a plateau while measuring nothing.
    """
    chunkings = {
        size: tuple(text for _, text in solution.build_chunks(solution.CORPUS, size=size))
        for size in solution.SWEEP_SIZES
    }
    assert len(set(chunkings.values())) == len(solution.SWEEP_SIZES)


def test_the_labelled_set_is_large_enough_to_resolve_a_difference():
    """Fifteen queries minimum, and every label names a real document."""
    assert len(solution.LABELLED_QUERIES) >= 15
    for query, relevant in solution.LABELLED_QUERIES:
        assert query.strip()
        assert relevant
        for document_id in relevant:
            assert document_id in solution.CORPUS


def test_hybrid_score_reduces_to_the_pure_strategies():
    """Alpha 0 is pure keyword and alpha 1 is pure vector."""
    assert solution.hybrid_score(0.8, 0.2, alpha=0.0) == 0.8
    assert solution.hybrid_score(0.8, 0.2, alpha=1.0) == 0.2


def test_keyword_ranking_drops_chunks_that_match_nothing():
    """A chunk with no overlapping token is not a weak hit, it is not a hit."""
    chunks = [
        ("a#0", "refund window and returns"),
        ("b#0", "completely unrelated wording here"),
    ]
    assert solution.keyword_ranked("refund", chunks) == ["a#0"]
    assert solution.keyword_ranked("nothing overlaps", chunks) == []


def test_keyword_ranking_breaks_ties_without_using_corpus_order():
    """Equally scoring chunks rank by id, not by the order they arrived in."""
    chunks = [
        ("z-doc#0", "refund policy text"),
        ("a-doc#0", "refund policy text"),
    ]
    forward = solution.keyword_ranked("refund", chunks)
    backward = solution.keyword_ranked("refund", list(reversed(chunks)))
    assert forward == backward == ["a-doc#0", "z-doc#0"]


def test_evaluate_reports_every_strategy_on_the_same_queries():
    """Step 6 returns one comparable number per strategy."""
    scores = solution.evaluate(solution.CORPUS, solution.LABELLED_QUERIES, k=1)
    assert set(scores) == {"vector", "keyword", "hybrid", "reranked"}
    assert all(0.0 <= value <= 1.0 for value in scores.values())


def test_evaluate_does_not_depend_on_the_order_of_the_corpus():
    """Reordering the corpus must not move any score.

    Declaration order is not a property of a retrieval strategy. A ranking
    that leaves ties to dict order reports a number that changes when the
    corpus is reordered, so a real improvement and a lucky ordering become
    indistinguishable.
    """
    baseline = solution.evaluate(solution.CORPUS, solution.LABELLED_QUERIES, k=1)
    for order in (
        list(reversed(solution.CORPUS)),
        sorted(solution.CORPUS),
    ):
        reordered = {key: solution.CORPUS[key] for key in order}
        assert solution.evaluate(reordered, solution.LABELLED_QUERIES, k=1) == baseline


def test_tune_alpha_reports_one_score_per_weight():
    """Alpha is measured on the labelled set rather than assumed."""
    alphas = [0.0, 0.5, 1.0]
    tuned = solution.tune_alpha(solution.CORPUS, solution.LABELLED_QUERIES, alphas, k=1)
    assert list(tuned) == alphas
    assert all(0.0 <= value <= 1.0 for value in tuned.values())


def test_the_alpha_endpoints_agree_with_the_pure_strategies():
    """Alpha 0 scores like keyword-only ranking and alpha 1 like vector-only.

    This is what makes the tuning curve readable: without it, a middle alpha
    winning could just mean the endpoints were computed differently.
    """
    tuned = solution.tune_alpha(solution.CORPUS, solution.LABELLED_QUERIES, [1.0], k=1)
    vector_only = solution.evaluate(solution.CORPUS, solution.LABELLED_QUERIES, k=1)
    assert tuned[1.0] == vector_only["vector"]


def test_split_queries_partitions_the_labelled_set():
    """The two halves are disjoint and together they are the original set.

    A knob chosen on the tuning half and reported on the held-out half is
    only honest if no query appears in both.
    """
    tuning, holdout = solution.split_queries(solution.LABELLED_QUERIES)
    assert tuning and holdout
    tuning_queries = [query for query, _ in tuning]
    holdout_queries = [query for query, _ in holdout]
    assert not set(tuning_queries) & set(holdout_queries)
    assert sorted(tuning + holdout) == sorted(solution.LABELLED_QUERIES)


def test_both_halves_cover_every_document():
    """Neither half can score a document the other half never asks about."""
    for half in solution.split_queries(solution.LABELLED_QUERIES):
        covered = {
            document_id for _, relevant in half for document_id in relevant
        }
        assert covered == set(solution.CORPUS)


def test_careful_score_sees_matches_that_plain_overlap_misses():
    """The reranker's scorer must not be the scorer it is meant to improve on."""
    text = "Refunds are issued to the original payment method"
    query = "When will my refund arrive?"
    assert solution.keyword_score(query, text) == 0.0
    assert solution.careful_score(query, text) > 0.0


def test_rerank_returns_a_permutation_of_its_input():
    """Reranked ids are a subset of the input with no duplicates or inventions."""
    hits = [
        solution.SearchHit("returns-policy#0", "returns are accepted", 0.9),
        solution.SearchHit("shipping-policy#0", "standard shipping takes", 0.8),
        solution.SearchHit("warranty-policy#0", "hardware carries a warranty", 0.7),
        solution.SearchHit("store-hours#0", "the store is open", 0.6),
    ]
    reranked = solution.rerank("when is the store open", hits, keep=3)
    input_ids = {hit.id for hit in hits}
    reranked_ids = [hit.id for hit in reranked]
    assert len(reranked) == 3
    assert len(set(reranked_ids)) == len(reranked_ids)
    assert set(reranked_ids) <= input_ids


def test_rerank_actually_reorders_by_the_careful_score():
    """The best candidate is promoted even when the cheap pass ranked it last.

    Without this the earlier permutation test passes for a reranker that
    returns hits[:keep] untouched, which is the one behaviour the step must
    not have.
    """
    hits = [
        solution.SearchHit("returns-policy#0", "returns are accepted", 0.9),
        solution.SearchHit("shipping-policy#0", "standard shipping takes", 0.8),
        solution.SearchHit("warranty-policy#0", "hardware carries a warranty", 0.7),
        solution.SearchHit("store-hours#0", "the store is open", 0.6),
    ]
    reranked = solution.rerank("when is the store open", hits, keep=3)
    assert reranked[0].id == "store-hours#0"


def test_rerank_does_not_depend_on_the_order_of_its_candidates():
    """The same shortlist in a different order reranks the same way."""
    hits = [
        solution.SearchHit("a#0", "the store is open", 0.5),
        solution.SearchHit("b#0", "the store is open", 0.5),
        solution.SearchHit("c#0", "unrelated wording", 0.4),
    ]
    forward = [hit.id for hit in solution.rerank("when is the store open", hits, keep=2)]
    backward = [
        hit.id
        for hit in solution.rerank("when is the store open", list(reversed(hits)), keep=2)
    ]
    assert forward == backward == ["a#0", "b#0"]
