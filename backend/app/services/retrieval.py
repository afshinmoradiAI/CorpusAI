"""BM25-based retrieval over chunks. No embeddings, no extra services.

For 5–30 reference PDFs (a few hundred chunks), BM25 ranks scientific
text well — the query and chunks share vocabulary. Swap for embeddings
later by replacing this class while keeping the public surface stable.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from rank_bm25 import BM25Okapi

from app.schemas.papers import Chunk, ChunkMatch

_TOKEN_RE = re.compile(r"[A-Za-z][A-Za-z0-9\-]*")


def _tokenise(text: str) -> list[str]:
    return [t.lower() for t in _TOKEN_RE.findall(text)]


@dataclass(slots=True)
class ChunkIndex:
    """Lazy BM25 index over a list of chunks. Rebuilds on `add`."""

    chunks: list[Chunk] = field(default_factory=list)
    _bm25: BM25Okapi | None = field(default=None, init=False, repr=False)
    _tokens: list[list[str]] = field(default_factory=list, init=False, repr=False)

    def add(self, new_chunks: list[Chunk]) -> None:
        self.chunks.extend(new_chunks)
        self._tokens.extend(_tokenise(c.text) for c in new_chunks)
        self._bm25 = BM25Okapi(self._tokens) if self._tokens else None

    def search(self, query: str, k: int = 5) -> list[ChunkMatch]:
        if not self.chunks or self._bm25 is None:
            return []
        scores = self._bm25.get_scores(_tokenise(query))
        ranked = sorted(
            zip(self.chunks, scores, strict=True),
            key=lambda pair: pair[1],
            reverse=True,
        )
        return [ChunkMatch(chunk=c, score=float(s)) for c, s in ranked[:k]]
