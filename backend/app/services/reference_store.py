"""Process-local store for uploaded reference sets.

Each `RefSet` is identified by a UUID (`set_id`) returned to the client at
upload time. The store holds:
- the metadata (filenames, page counts)
- the parsed chunks
- a BM25 index built over the chunks

This is intentionally NOT persistent — restarts wipe state. Suitable for
single-process MVP; replace with a real DB / vector store when scaling.
"""

from __future__ import annotations

import asyncio
import uuid
from dataclasses import dataclass, field

from app.schemas.papers import RefSet, UploadedRef
from app.services.chunker import chunk_pages
from app.services.pdf_reader import read_pdf_bytes
from app.services.retrieval import ChunkIndex


@dataclass(slots=True)
class _Entry:
    meta: RefSet
    index: ChunkIndex = field(default_factory=ChunkIndex)


class ReferenceStore:
    def __init__(self) -> None:
        self._entries: dict[str, _Entry] = {}
        self._lock = asyncio.Lock()

    async def create_set(self, files: list[tuple[str, bytes]]) -> RefSet:
        """Parse, chunk, and index a batch of uploaded PDFs in one set."""
        set_id = str(uuid.uuid4())
        documents: list[UploadedRef] = []
        index = ChunkIndex()

        for filename, data in files:
            ref_id = str(uuid.uuid4())
            pages = read_pdf_bytes(data)
            chunks = chunk_pages(pages, ref_id=ref_id)
            documents.append(
                UploadedRef(
                    ref_id=ref_id,
                    filename=filename,
                    page_count=len(pages),
                    char_count=sum(len(p.text) for p in pages),
                )
            )
            index.add(chunks)

        meta = RefSet(set_id=set_id, documents=documents)
        async with self._lock:
            self._entries[set_id] = _Entry(meta=meta, index=index)
        return meta

    def get_meta(self, set_id: str) -> RefSet | None:
        entry = self._entries.get(set_id)
        return entry.meta if entry else None

    def get_index(self, set_id: str) -> ChunkIndex | None:
        entry = self._entries.get(set_id)
        return entry.index if entry else None


_store: ReferenceStore | None = None


def get_reference_store() -> ReferenceStore:
    global _store
    if _store is None:
        _store = ReferenceStore()
    return _store
