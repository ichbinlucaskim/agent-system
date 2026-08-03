"""Tests for Lab 08 - RAG basics.

Chunking, the hash-based embedding stub, search, and sqlite3 persistence are
all deterministic and are tested offline. Only the grounded generation step
would need an API key, and no test here calls it.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest


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
solution = _load("lab08_solution", LAB_ROOT / "solution" / "main.py")


def test_chunk_respects_the_size_setting():
    """No chunk is meaningfully longer than the requested size."""
    text = " ".join(f"word{i}" for i in range(400))
    chunks = solution.chunk(text, size=100, overlap=20)
    assert len(chunks) > 1
    # Snapping to a word boundary may run a few characters past size, but a
    # chunk twice the size would mean the window logic is broken.
    assert all(len(piece) <= 120 for piece in chunks)


def test_chunk_overlaps_adjacent_windows():
    """Consecutive chunks share text, so a boundary sentence stays retrievable."""
    text = " ".join(f"word{i}" for i in range(200))
    chunks = solution.chunk(text, size=100, overlap=40)
    assert len(chunks) > 1
    for first, second in zip(chunks, chunks[1:]):
        shared = set(first.split()) & set(second.split())
        assert shared


def test_chunk_rejects_an_overlap_that_would_not_advance():
    """overlap >= size can never advance the window, so it raises."""
    with pytest.raises(ValueError):
        solution.chunk("some text", size=50, overlap=50)
    with pytest.raises(ValueError):
        solution.chunk("some text", size=50, overlap=80)


def test_embed_is_deterministic():
    """The same text always embeds to the identical vector."""
    text = "returns are accepted within 30 days"
    first = solution.embed(text)
    second = solution.embed(text)
    assert (first == second).all()


def test_embed_returns_the_requested_dimension():
    """Vector length equals dim regardless of the text length."""
    assert solution.embed("hi", dim=64).shape == (64,)
    assert solution.embed(" ".join(["token"] * 500), dim=64).shape == (64,)
    assert solution.embed("hi", dim=256).shape == (256,)


def test_search_retrieves_the_chunk_containing_the_answer():
    """A query about returns ranks a returns-policy chunk first."""
    store = solution.build_store(solution.CORPUS, size=160, overlap=40)
    hits = solution.search(store, "When are refunds issued after a return?", k=3)
    assert hits
    assert hits[0].id.startswith("returns-policy")


def test_the_store_survives_a_save_and_load_round_trip(tmp_path):
    """Search results are identical after a sqlite3 save and load."""
    store = solution.build_store(solution.CORPUS, size=160, overlap=40)
    query = "how long is the hardware warranty"
    before = [(hit.id, hit.text) for hit in solution.search(store, query)]

    path = tmp_path / "store.sqlite3"
    store.save(path)
    reloaded = type(store).load(path)
    after = [(hit.id, hit.text) for hit in solution.search(reloaded, query)]
    assert before == after
