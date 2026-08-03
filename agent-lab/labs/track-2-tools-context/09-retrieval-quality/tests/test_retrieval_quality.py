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
    sizes = [100, 200, 400]
    results = solution.sweep_chunk_sizes(
        solution.CORPUS, solution.LABELLED_QUERIES, sizes, k=3
    )
    assert list(results) == sizes
    assert all(0.0 <= recall <= 1.0 for recall in results.values())


def test_hybrid_score_reduces_to_the_pure_strategies():
    """Alpha 0 is pure keyword and alpha 1 is pure vector."""
    assert solution.hybrid_score(0.8, 0.2, alpha=0.0) == 0.8
    assert solution.hybrid_score(0.8, 0.2, alpha=1.0) == 0.2


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
