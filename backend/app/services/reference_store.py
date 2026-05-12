"""Persistent reference store backed by SQLite.

Each `RefSet` is identified by a UUID (`set_id`) returned to the client at
upload time. The store holds:
- the metadata (filenames, page counts)         → `ref_sets` + `documents`
- the parsed chunks                              → `chunks`
- a BM25 index built lazily over the chunks      → in-process LRU cache

Sets are scoped to a `user_id`; the API derives this from the authenticated
caller. Reads check ownership before returning data — anonymous sets created
without a user_id are visible to all (legacy / dev mode).
"""

from __future__ import annotations

import asyncio
import sqlite3
import time
import uuid
from collections import OrderedDict
from contextlib import contextmanager
from pathlib import Path
from threading import Lock
from typing import Iterator

from app.core.config import get_settings
from app.schemas.papers import Chunk, RefSet, UploadedRef
from app.services.chunker import chunk_pages
from app.services.pdf_reader import read_pdf_bytes
from app.services.retrieval import ChunkIndex

_SCHEMA = """
CREATE TABLE IF NOT EXISTS ref_sets (
    set_id     TEXT PRIMARY KEY,
    user_id    TEXT,
    created_at REAL NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_ref_sets_user ON ref_sets(user_id);

CREATE TABLE IF NOT EXISTS documents (
    ref_id     TEXT PRIMARY KEY,
    set_id     TEXT NOT NULL REFERENCES ref_sets(set_id) ON DELETE CASCADE,
    filename   TEXT NOT NULL,
    page_count INTEGER NOT NULL,
    char_count INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_documents_set ON documents(set_id);

CREATE TABLE IF NOT EXISTS chunks (
    chunk_id TEXT PRIMARY KEY,
    set_id   TEXT NOT NULL REFERENCES ref_sets(set_id) ON DELETE CASCADE,
    ref_id   TEXT NOT NULL,
    page     INTEGER NOT NULL,
    text     TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_chunks_set ON chunks(set_id);
"""


class ReferenceStoreError(RuntimeError):
    """Raised when the caller does not own / cannot access a set_id."""


class ReferenceStore:
    def __init__(self, db_path: Path) -> None:
        self._db_path = db_path
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        self._write_lock = asyncio.Lock()
        self._index_cache: OrderedDict[str, ChunkIndex] = OrderedDict()
        self._index_cache_lock = Lock()
        self._index_cache_max = 32
        with self._conn() as conn:
            conn.executescript(_SCHEMA)

    @contextmanager
    def _conn(self) -> Iterator[sqlite3.Connection]:
        conn = sqlite3.connect(self._db_path, isolation_level=None)
        conn.execute("PRAGMA foreign_keys = ON")
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    async def create_set(
        self,
        files: list[tuple[str, bytes]],
        *,
        user_id: str | None = None,
    ) -> RefSet:
        set_id = str(uuid.uuid4())
        documents: list[UploadedRef] = []
        all_chunks: list[Chunk] = []

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
            all_chunks.extend(chunks)

        async with self._write_lock:
            with self._conn() as conn:
                conn.execute(
                    "INSERT INTO ref_sets(set_id, user_id, created_at) VALUES (?, ?, ?)",
                    (set_id, user_id, time.time()),
                )
                conn.executemany(
                    "INSERT INTO documents(ref_id, set_id, filename, page_count, char_count) "
                    "VALUES (?, ?, ?, ?, ?)",
                    [
                        (d.ref_id, set_id, d.filename, d.page_count, d.char_count)
                        for d in documents
                    ],
                )
                conn.executemany(
                    "INSERT INTO chunks(chunk_id, set_id, ref_id, page, text) "
                    "VALUES (?, ?, ?, ?, ?)",
                    [
                        (c.chunk_id, set_id, c.ref_id, c.page, c.text)
                        for c in all_chunks
                    ],
                )
        return RefSet(set_id=set_id, documents=documents)

    def _check_owner(
        self, conn: sqlite3.Connection, set_id: str, user_id: str | None
    ) -> str | None:
        """Return the owner user_id if accessible, else None.

        Access is granted when:
        - the requested set is owned by `user_id`, or
        - the requested set has no owner (anonymous / dev mode), or
        - `user_id` is None (legacy callers / dev mode)
        """
        row = conn.execute(
            "SELECT user_id FROM ref_sets WHERE set_id = ?", (set_id,)
        ).fetchone()
        if row is None:
            return None
        owner = row["user_id"]
        if owner is None or user_id is None or owner == user_id:
            return owner
        raise ReferenceStoreError(f"set_id {set_id} not accessible to this user")

    def get_meta(self, set_id: str, *, user_id: str | None = None) -> RefSet | None:
        with self._conn() as conn:
            try:
                self._check_owner(conn, set_id, user_id)
            except ReferenceStoreError:
                return None
            row = conn.execute(
                "SELECT 1 FROM ref_sets WHERE set_id = ?", (set_id,)
            ).fetchone()
            if row is None:
                return None
            docs = conn.execute(
                "SELECT ref_id, filename, page_count, char_count "
                "FROM documents WHERE set_id = ? ORDER BY filename",
                (set_id,),
            ).fetchall()
        return RefSet(
            set_id=set_id,
            documents=[
                UploadedRef(
                    ref_id=d["ref_id"],
                    filename=d["filename"],
                    page_count=d["page_count"],
                    char_count=d["char_count"],
                )
                for d in docs
            ],
        )

    def get_index(
        self, set_id: str, *, user_id: str | None = None
    ) -> ChunkIndex | None:
        with self._conn() as conn:
            try:
                self._check_owner(conn, set_id, user_id)
            except ReferenceStoreError:
                return None
            row = conn.execute(
                "SELECT 1 FROM ref_sets WHERE set_id = ?", (set_id,)
            ).fetchone()
            if row is None:
                return None
            with self._index_cache_lock:
                if set_id in self._index_cache:
                    self._index_cache.move_to_end(set_id)
                    return self._index_cache[set_id]
            chunks_rows = conn.execute(
                "SELECT chunk_id, ref_id, page, text FROM chunks WHERE set_id = ?",
                (set_id,),
            ).fetchall()
        index = ChunkIndex()
        index.add(
            [
                Chunk(
                    chunk_id=r["chunk_id"],
                    ref_id=r["ref_id"],
                    page=r["page"],
                    text=r["text"],
                )
                for r in chunks_rows
            ]
        )
        with self._index_cache_lock:
            self._index_cache[set_id] = index
            self._index_cache.move_to_end(set_id)
            while len(self._index_cache) > self._index_cache_max:
                self._index_cache.popitem(last=False)
        return index

    def delete_set(self, set_id: str, *, user_id: str | None = None) -> bool:
        """Delete a set and all its rows. Returns True if a row was removed.

        Raises ReferenceStoreError if the caller is not the owner. Returns
        False if the set does not exist.
        """
        with self._conn() as conn:
            try:
                self._check_owner(conn, set_id, user_id)
            except ReferenceStoreError:
                raise
            cur = conn.execute(
                "DELETE FROM ref_sets WHERE set_id = ?", (set_id,)
            )
            removed = cur.rowcount > 0
        if removed:
            with self._index_cache_lock:
                self._index_cache.pop(set_id, None)
        return removed

    def list_sets(self, *, user_id: str | None = None) -> list[str]:
        with self._conn() as conn:
            if user_id is None:
                rows = conn.execute(
                    "SELECT set_id FROM ref_sets ORDER BY created_at DESC"
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT set_id FROM ref_sets "
                    "WHERE user_id = ? OR user_id IS NULL "
                    "ORDER BY created_at DESC",
                    (user_id,),
                ).fetchall()
        return [r["set_id"] for r in rows]


_store: ReferenceStore | None = None


def get_reference_store() -> ReferenceStore:
    global _store
    if _store is None:
        settings = get_settings()
        _store = ReferenceStore(Path(settings.data_dir) / "corpusai.sqlite")
    return _store


def reset_reference_store() -> None:
    """For tests — clear the singleton so the next call uses fresh config."""
    global _store
    _store = None
