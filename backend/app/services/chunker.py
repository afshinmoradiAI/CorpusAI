"""Group per-page text into retrievable chunks.

Strategy: split each page into paragraphs (blank-line delimited), then pack
paragraphs into chunks with a target word count. Each chunk records the
page where its first paragraph started.
"""

from __future__ import annotations

import re
import uuid
from collections.abc import Iterable

from app.schemas.papers import Chunk
from app.services.pdf_reader import PageText

_TARGET_WORDS = 350
_MAX_WORDS = 500
_BLANK_LINE = re.compile(r"\n\s*\n+")


def chunk_pages(pages: Iterable[PageText], ref_id: str) -> list[Chunk]:
    chunks: list[Chunk] = []
    buf: list[str] = []
    buf_words = 0
    buf_page: int | None = None

    def flush() -> None:
        nonlocal buf, buf_words, buf_page
        if not buf:
            return
        chunks.append(
            Chunk(
                chunk_id=str(uuid.uuid4()),
                ref_id=ref_id,
                text="\n\n".join(buf).strip(),
                page=buf_page or 1,
            )
        )
        buf = []
        buf_words = 0
        buf_page = None

    for page in pages:
        for para in _split_paragraphs(page.text):
            words = para.split()
            if not words:
                continue
            if buf_page is None:
                buf_page = page.page
            if buf_words + len(words) > _MAX_WORDS and buf:
                flush()
                buf_page = page.page
            buf.append(para)
            buf_words += len(words)
            if buf_words >= _TARGET_WORDS:
                flush()

    flush()
    return chunks


def _split_paragraphs(text: str) -> list[str]:
    return [p.strip() for p in _BLANK_LINE.split(text) if p.strip()]
