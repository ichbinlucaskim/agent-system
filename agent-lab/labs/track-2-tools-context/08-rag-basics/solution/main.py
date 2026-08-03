"""Lab 08 - RAG basics (reference solution).

A retrieval pipeline end to end: chunk documents, embed them with a
deterministic local stub, search by cosine similarity, and generate an answer
that is grounded in the retrieved passages and cites them.
"""

from __future__ import annotations

import hashlib
import re
from pathlib import Path
from typing import Any

import numpy as np

from common.client import MissingAPIKeyError, complete, text_of
from common.vectorstore import SearchHit, VectorStore

CORPUS: dict[str, str] = {
    "returns-policy": (
        "Returns are accepted within 30 days of delivery. Refunds are issued "
        "to the original payment method within 5 business days of receipt. "
        "Items must be returned in their original packaging with proof of "
        "purchase. Opened software and clearance items cannot be returned."
    ),
    "shipping-policy": (
        "Standard shipping takes 3 to 5 business days. Express shipping "
        "arrives the next business day for orders placed before 2pm. "
        "Orders over 50 dollars ship free with the standard option. "
        "International shipping is not currently offered."
    ),
    "warranty-policy": (
        "Hardware carries a 12 month warranty covering manufacturing defects. "
        "Accidental damage is not covered by the warranty. Warranty claims "
        "require the original receipt and the product serial number. "
        "Approved claims are repaired or replaced within 10 business days."
    ),
}


def chunk(text: str, *, size: int = 400, overlap: int = 50) -> list[str]:
    """Split text into overlapping windows of roughly `size` characters."""
    if overlap >= size:
        # With overlap >= size the window never advances and the loop below
        # would run forever, so reject the configuration up front.
        raise ValueError(f"overlap ({overlap}) must be smaller than size ({size})")
    text = " ".join(text.split())
    if not text:
        return []
    chunks: list[str] = []
    start = 0
    while start < len(text):
        end = min(start + size, len(text))
        if end < len(text):
            # Prefer a sentence end, then any whitespace, over cutting a word
            # in half. A half word embeds as a token nothing will query for.
            window = text[start:end]
            sentence_cut = max(
                window.rfind(". "), window.rfind("? "), window.rfind("! ")
            )
            if sentence_cut > 0:
                end = start + sentence_cut + 1
            elif (space_cut := window.rfind(" ")) > 0:
                end = start + space_cut
        chunks.append(text[start:end].strip())
        if end >= len(text):
            break
        # The overlap keeps a sentence that straddles the boundary present in
        # both windows, so it stays retrievable from either side. The new
        # start snaps back to a word boundary so no window opens mid-word.
        next_start = max(end - overlap, start + 1)
        boundary = text.rfind(" ", start + 1, next_start + 1) + 1
        start = boundary if boundary > start else next_start
    return chunks


def embed(text: str, *, dim: int = 256) -> np.ndarray:
    """Deterministic hash-based embedding stub. No API, no key, no network."""
    vector = np.zeros(dim, dtype=np.float32)
    for token in re.findall(r"\w+", text.lower()):
        # The builtin hash() is salted per process, which would make vectors
        # differ across runs. md5 is stable everywhere and speed is fine here.
        digest = hashlib.md5(token.encode("utf-8")).digest()
        vector[int.from_bytes(digest[:4], "big") % dim] += 1.0
    norm = float(np.linalg.norm(vector))
    if norm > 0.0:
        vector /= norm
    return vector


def build_store(
    documents: dict[str, str], *, size: int = 400, overlap: int = 50
) -> VectorStore:
    """Chunk and embed every document into a VectorStore."""
    store = VectorStore()
    for document_id, text in documents.items():
        for index, piece in enumerate(chunk(text, size=size, overlap=overlap)):
            # The id names both the source and the chunk index, so a citation
            # like returns-policy#2 is traceable back to its document.
            store.add(f"{document_id}#{index}", piece, embed(piece))
    return store


def search(store: VectorStore, query: str, k: int = 3) -> list[SearchHit]:
    """Embed the query and return the k most similar chunks."""
    # The query must go through the same embedding function as the chunks;
    # scores between two different embedding spaces are meaningless.
    return store.search(embed(query), k)


def answer(query: str, store: VectorStore, k: int = 3) -> dict[str, Any]:
    """Generate an answer grounded in the retrieved chunks, with citations."""
    hits = search(store, query, k)
    chunk_ids = [hit.id for hit in hits]
    if hits:
        blocks = "\n\n".join(f"[{hit.id}] {hit.text}" for hit in hits)
    else:
        blocks = "(no passages matched this question)"
    system = (
        "You answer questions using only the reference passages below.\n\n"
        "Rules:\n"
        "- Cite the passage id in square brackets for every claim.\n"
        "- If the passages do not cover the question, say you do not know. "
        "Never answer from general knowledge and never invent a citation.\n\n"
        f"Reference passages:\n{blocks}"
    )
    response = complete([{"role": "user", "content": query}], system=system)
    # The ids ride along with the answer so a caller or a test can check that
    # the cited passage actually says what the answer claims.
    return {"answer": text_of(response), "chunk_ids": chunk_ids}


def main() -> int:
    """Build the store, search it, round trip it through sqlite3, then answer."""
    # A small size makes every document span several chunks, so the pipeline
    # mechanics are visible in the output.
    store = build_store(CORPUS, size=160, overlap=40)
    print(f"store holds {len(store)} chunks from {len(CORPUS)} documents\n")

    # The stub embedding matches exact tokens only, so the demo query reuses
    # corpus vocabulary. A real embedding model would also catch paraphrases.
    query = "When are refunds issued after a return?"
    print(f"query: {query}")
    hits = search(store, query)
    for hit in hits:
        print(f"  {hit.score:.3f}  [{hit.id}] {hit.text[:60]}...")

    path = Path(__file__).resolve().parents[1] / "data" / "rag-store.sqlite3"
    store.save(path)
    reloaded = VectorStore.load(path)
    same = [hit.id for hit in search(reloaded, query)] == [hit.id for hit in hits]
    print(f"\nsave and load round trip identical: {same}")

    try:
        result = answer(query, store)
    except MissingAPIKeyError as error:
        print(f"skipping generation: {error}")
        return 0
    print(f"\nanswer: {result['answer']}")
    print(f"retrieved ids: {result['chunk_ids']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
