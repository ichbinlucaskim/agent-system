"""Policy retrieval with the lab 08 hash embedding stub.

Purpose
    Load policy markdown, chunk it, embed with a deterministic hash vector, and
    search via ``common.vectorstore`` so FAQ and tools can cite written rules.

Why
    Written policy must be retrievable as reference data without network or API
    keys. The hash stub keeps demos and eval offline while preserving the same
    retrieve → wrap → cite shape as a real embedding stack.

Trade-offs
    Hash embeddings are weak on paraphrase; teaching corpus and keyword overlap
    elsewhere compensate. Chunk size/overlap are fixed defaults (400/50).

Edges
    Empty documents yield no chunks. Invalid chunk size/overlap raise
    ``ValueError``. Search embeds the query with the same ``embed`` function.
"""

from __future__ import annotations

import hashlib
import re
from pathlib import Path

import numpy as np

from common.vectorstore import SearchHit, VectorStore
from support_desk.paths import POLICY_DIR


def embed(text: str, *, dim: int = 256) -> np.ndarray:
    """Deterministic hash-based embedding stub. No API, no key, no network.

    Purpose
        Map tokenized text to a unit L2 vector of length ``dim``.

    Why
        Offline lab constraint: retrieval must work without Anthropic/OpenAI
        embedding endpoints.

    Trade-offs
        Collision-prone and semantics-poor; good for demos, not production
        ranking quality.

    Edges
        Empty / no-token text → zero vector (norm 0, no divide). Tokens are
        ``\\w+`` lowercased.
    """
    vector = np.zeros(dim, dtype=np.float32)
    for token in re.findall(r"\w+", text.lower()):
        digest = hashlib.md5(token.encode("utf-8")).digest()
        vector[int.from_bytes(digest[:4], "big") % dim] += 1.0
    norm = float(np.linalg.norm(vector))
    if norm > 0.0:
        vector /= norm
    return vector


def chunk(text: str, *, size: int = 400, overlap: int = 50) -> list[str]:
    """Split text into overlapping character windows.

    Purpose
        Produce passage-sized pieces for the vector store.

    Why
        Policy files are longer than a single retrieval unit; overlap reduces
        boundary misses on consecutive sentences.

    Trade-offs
        Character windows, not sentence-aware—may cut mid-word at boundaries.

    Edges
        Blank → ``[]``. ``size <= 0`` or bad overlap → ``ValueError``.
    """
    text = text.strip()
    if not text:
        return []
    if size <= 0:
        raise ValueError("size must be positive")
    if overlap < 0 or overlap >= size:
        raise ValueError("overlap must be >= 0 and < size")
    pieces: list[str] = []
    start = 0
    while start < len(text):
        end = min(start + size, len(text))
        pieces.append(text[start:end])
        if end >= len(text):
            break
        start = end - overlap
    return pieces


def load_policy_documents(policy_dir: Path | None = None) -> dict[str, str]:
    """Read all ``*.md`` policy files keyed by stem.

    Purpose
        Load the on-disk policy corpus into memory.

    Why
        Separates IO from indexing so tests can inject document dicts.

    Trade-offs
        Only top-level ``*.md``; no recursion. Sorted by path for stable ids.

    Edges
        Missing directory → empty dict from ``glob`` (no files). Encoding is
        UTF-8.
    """
    root = policy_dir or POLICY_DIR
    documents: dict[str, str] = {}
    for path in sorted(root.glob("*.md")):
        documents[path.stem] = path.read_text(encoding="utf-8")
    return documents


def build_policy_store(
    documents: dict[str, str] | None = None,
    *,
    size: int = 400,
    overlap: int = 50,
) -> VectorStore:
    """Chunk, embed, and index policy documents into a VectorStore.

    Purpose
        Return a ready-to-search store for FAQ and ``search_policy`` tool.

    Why
        One builder keeps chunk/embed parameters consistent across CLI, HTTP,
        and eval contexts.

    Trade-offs
        Rebuilds from scratch each call—fine for small corpora, not for huge
        libraries.

    Edges
        Ids are ``{document_id}#{index}``. ``documents is None`` loads from disk.
    """
    docs = documents if documents is not None else load_policy_documents()
    store = VectorStore()
    for document_id, text in docs.items():
        for index, piece in enumerate(chunk(text, size=size, overlap=overlap)):
            store.add(f"{document_id}#{index}", piece, embed(piece))
    return store


def search_policy(store: VectorStore, query: str, k: int = 3) -> list[SearchHit]:
    """Embed the query and return top-k policy hits.

    Purpose
        Thin wrapper so callers never touch embedding details.

    Why
        Keeps FAQ path and tools on the same retrieval API.

    Trade-offs
        Default ``k=3`` matches tool behavior; callers can override.

    Edges
        Empty store or zero query vector may yield empty / weak hits depending
        on ``VectorStore.search``.
    """
    return store.search(embed(query), k)
