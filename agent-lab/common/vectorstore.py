"""A small in-memory vector store with optional sqlite3 persistence.

No cloud account and no external vector database. Vectors live in a numpy
array, similarity is plain cosine, and persistence is a single sqlite3 file
from the standard library. That is enough to teach retrieval; swapping in a
production store later changes the storage layer, not the ideas.
"""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from pathlib import Path

import numpy as np


@dataclass(frozen=True)
class SearchHit:
    """One retrieval result."""

    id: str
    text: str
    score: float


class VectorStore:
    """Stores (id, text, vector) triples and searches them by cosine similarity."""

    def __init__(self) -> None:
        self._ids: list[str] = []
        self._texts: list[str] = []
        self._vectors: list[np.ndarray] = []

    def __len__(self) -> int:
        return len(self._ids)

    def add(self, id: str, text: str, vector: np.ndarray | list[float]) -> None:
        """Add or replace one record. Re-adding an existing id overwrites it."""
        array = np.asarray(vector, dtype=np.float32).ravel()
        if array.size == 0:
            raise ValueError("vector must not be empty")
        if self._vectors and array.size != self._vectors[0].size:
            raise ValueError(
                f"vector has dimension {array.size}, store expects "
                f"{self._vectors[0].size}"
            )
        if id in self._ids:
            index = self._ids.index(id)
            self._texts[index] = text
            self._vectors[index] = array
            return
        self._ids.append(id)
        self._texts.append(text)
        self._vectors.append(array)

    def search(self, vector: np.ndarray | list[float], k: int = 3) -> list[SearchHit]:
        """Return the k most similar records, highest cosine similarity first."""
        if not self._vectors or k <= 0:
            return []
        query = np.asarray(vector, dtype=np.float32).ravel()
        matrix = np.vstack(self._vectors)
        norms = np.linalg.norm(matrix, axis=1) * np.linalg.norm(query)
        # Guard against zero vectors so that a bad record scores 0, not NaN.
        norms = np.where(norms == 0.0, 1e-12, norms)
        scores = (matrix @ query) / norms
        order = np.argsort(-scores)[:k]
        return [
            SearchHit(self._ids[i], self._texts[i], float(scores[i])) for i in order
        ]

    def save(self, path: str | Path) -> None:
        """Persist every record to a sqlite3 file, replacing prior contents."""
        connection = sqlite3.connect(str(path))
        try:
            connection.execute("DROP TABLE IF EXISTS records")
            connection.execute(
                "CREATE TABLE records (id TEXT PRIMARY KEY, text TEXT, vector TEXT)"
            )
            connection.executemany(
                "INSERT INTO records (id, text, vector) VALUES (?, ?, ?)",
                [
                    (self._ids[i], self._texts[i], json.dumps(self._vectors[i].tolist()))
                    for i in range(len(self._ids))
                ],
            )
            connection.commit()
        finally:
            connection.close()

    @classmethod
    def load(cls, path: str | Path) -> "VectorStore":
        """Rebuild a store from a sqlite3 file written by save."""
        store = cls()
        connection = sqlite3.connect(str(path))
        try:
            rows = connection.execute("SELECT id, text, vector FROM records").fetchall()
        finally:
            connection.close()
        for record_id, text, vector_json in rows:
            store.add(record_id, text, json.loads(vector_json))
        return store
