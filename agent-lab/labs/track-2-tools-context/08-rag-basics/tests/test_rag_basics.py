"""Tests for Lab 08 - RAG basics.

Each test names the behaviour the lab must produce and describes its
assertion in a comment. The bodies skip until the lab is implemented:
replace the skip with the real assertion as you build each piece.
"""

from __future__ import annotations

import pytest


def test_chunk_respects_the_size_setting():
    # Assert no chunk is meaningfully longer than the requested size.
    pytest.skip("Lab not implemented yet")


def test_chunk_overlaps_adjacent_windows():
    # Assert consecutive chunks share text, so a sentence on a boundary stays retrievable.
    pytest.skip("Lab not implemented yet")


def test_chunk_rejects_an_overlap_that_would_not_advance():
    # Assert overlap greater than or equal to size raises rather than looping forever.
    pytest.skip("Lab not implemented yet")


def test_embed_is_deterministic():
    # Assert embedding the same text twice returns identical vectors.
    pytest.skip("Lab not implemented yet")


def test_embed_returns_the_requested_dimension():
    # Assert the vector length equals dim for texts of very different lengths.
    pytest.skip("Lab not implemented yet")


def test_search_retrieves_the_chunk_containing_the_answer():
    # Assert a query about returns ranks the returns chunk first.
    pytest.skip("Lab not implemented yet")


def test_the_store_survives_a_save_and_load_round_trip():
    # Assert search results are identical after saving to sqlite3 and loading into a new store.
    pytest.skip("Lab not implemented yet")
