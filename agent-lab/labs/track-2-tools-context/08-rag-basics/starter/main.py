"""Lab 08 - RAG basics (starter).

Goal: Build a retrieval pipeline end to end: chunk documents, embed them with a deterministic local stub, search by cosine similarity, and generate an answer that is grounded in the retrieved passages and cites them.

Fill in each function below. Every one carries a TODO describing what to
do and which step of the README it maps to. Run the tests with:

    pytest labs/track-2-tools-context/08-rag-basics/tests -v
"""

from __future__ import annotations

from typing import Any

import numpy as np

from common.vectorstore import SearchHit, VectorStore

# A few short policy documents to retrieve from. Keep them small enough that
# you can check a citation by eye, and make sure they disagree about nothing,
# so a wrong answer means the pipeline is wrong rather than the corpus.
CORPUS: dict[str, str] = {}


def chunk(text: str, *, size: int = 400, overlap: int = 50) -> list[str]:
    """Split text into overlapping windows of roughly `size` characters."""
    # TODO: step 1. Prefer sentence or paragraph boundaries over cutting mid-word. Overlap keeps a sentence that straddles a boundary retrievable. Guard against overlap >= size, which would loop forever.
    raise NotImplementedError


def embed(text: str, *, dim: int = 256) -> np.ndarray:
    """Deterministic hash-based embedding stub. No API, no key, no network."""
    # TODO: step 2. Hash each token to an index in range(dim), accumulate counts, and normalise to unit length. The same text must always return the same vector.
    raise NotImplementedError


def build_store(documents: dict[str, str], *, size: int = 400, overlap: int = 50) -> VectorStore:
    """Chunk and embed every document into a VectorStore."""
    # TODO: step 3. Use an id that names both the source document and the chunk index, for example 'returns-policy#2', so a citation is traceable back to its source.
    raise NotImplementedError


def search(store: VectorStore, query: str, k: int = 3) -> list[SearchHit]:
    """Embed the query and return the k most similar chunks."""
    # TODO: step 4. Embed the query with the same function used for the chunks. A different embedding function on either side makes the scores meaningless.
    raise NotImplementedError


def answer(query: str, store: VectorStore, k: int = 3) -> dict[str, Any]:
    """Generate an answer grounded in the retrieved chunks, with citations."""
    # TODO: step 5. Put the retrieved chunks in the system prompt labelled by id, require a citation per claim, and require a refusal when the chunks do not cover the question. Return {'answer': ..., 'chunk_ids': [...]} so the citation is checkable.
    raise NotImplementedError


def main() -> int:
    """Run the lab end to end and print what happened."""
    # TODO: step 6. Save the store to data/ as sqlite3 and load it back. Then
    # check the harder half: a *new process* must rank the same chunks in the
    # same order. That is the whole reason step 2 hashes with md5 instead of
    # the builtin hash, which is salted per process and would silently rank
    # the wrong chunk first on the next run. A same-process round trip passes
    # either way, so it cannot tell you anything about this.
    #
    # TODO: final step. Wire the functions above together and print
    # enough that the behaviour described in the README is visible.
    raise NotImplementedError


if __name__ == "__main__":
    raise SystemExit(main())
