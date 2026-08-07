"""Policy retrieval with the lab 08 hash embedding stub."""

from __future__ import annotations

import hashlib
import re
from pathlib import Path

import numpy as np

from common.vectorstore import SearchHit, VectorStore
from support_desk.paths import POLICY_DIR


def embed(text: str, *, dim: int = 256) -> np.ndarray:
    """Deterministic hash-based embedding stub. No API, no key, no network."""
    vector = np.zeros(dim, dtype=np.float32)
    for token in re.findall(r"\w+", text.lower()):
        digest = hashlib.md5(token.encode("utf-8")).digest()
        vector[int.from_bytes(digest[:4], "big") % dim] += 1.0
    norm = float(np.linalg.norm(vector))
    if norm > 0.0:
        vector /= norm
    return vector


def chunk(text: str, *, size: int = 400, overlap: int = 50) -> list[str]:
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
    docs = documents if documents is not None else load_policy_documents()
    store = VectorStore()
    for document_id, text in docs.items():
        for index, piece in enumerate(chunk(text, size=size, overlap=overlap)):
            store.add(f"{document_id}#{index}", piece, embed(piece))
    return store


def search_policy(store: VectorStore, query: str, k: int = 3) -> list[SearchHit]:
    return store.search(embed(query), k)
