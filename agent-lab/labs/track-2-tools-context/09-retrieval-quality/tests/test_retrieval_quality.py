"""Tests for Lab 09 - Retrieval quality.

Each test names the behaviour the lab must produce and describes its
assertion in a comment. The bodies skip until the lab is implemented:
replace the skip with the real assertion as you build each piece.
"""

from __future__ import annotations

import pytest


def test_recall_at_k_matches_a_hand_counted_example():
    # Assert that with two relevant ids and one of them in the top 3, recall is 0.5.
    pytest.skip("Lab not implemented yet")


def test_recall_at_k_only_considers_the_first_k():
    # Assert a relevant id at position k+1 does not count.
    pytest.skip("Lab not implemented yet")


def test_recall_at_k_handles_an_empty_relevant_list():
    # Assert the documented edge-case value is returned rather than raising a ZeroDivisionError.
    pytest.skip("Lab not implemented yet")


def test_sweep_returns_one_entry_per_chunk_size():
    # Assert the result has exactly the requested sizes as keys.
    pytest.skip("Lab not implemented yet")


def test_hybrid_score_reduces_to_the_pure_strategies():
    # Assert alpha 0 returns the keyword score and alpha 1 returns the vector score.
    pytest.skip("Lab not implemented yet")


def test_rerank_returns_a_permutation_of_its_input():
    # Assert the reranked ids are a subset of the input ids with no duplicates and no invented entries.
    pytest.skip("Lab not implemented yet")
