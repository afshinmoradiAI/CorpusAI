"""Extract per-page plain text from a PDF using `pypdf` (pure Python).

We keep page boundaries because downstream chunks carry a `page` field —
useful for citation hints in the writing agents and for the UI to deep-link.
"""

from __future__ import annotations

import io
from dataclasses import dataclass

from pypdf import PdfReader
from pypdf.errors import PdfReadError as _PypdfReadError


class PDFReadError(RuntimeError):
    """Raised when a file cannot be parsed as a PDF."""


@dataclass(slots=True)
class PageText:
    page: int  # 1-indexed
    text: str


def read_pdf_bytes(data: bytes) -> list[PageText]:
    """Parse a PDF supplied as raw bytes (e.g. from an HTTP upload)."""
    try:
        reader = PdfReader(io.BytesIO(data))
    except (_PypdfReadError, OSError, ValueError) as exc:
        raise PDFReadError(f"Could not open PDF: {exc}") from exc

    pages: list[PageText] = []
    for i, page in enumerate(reader.pages):
        try:
            text = page.extract_text() or ""
        except Exception as exc:  # noqa: BLE001 — pypdf raises mixed exceptions
            raise PDFReadError(f"Could not extract page {i + 1}: {exc}") from exc
        pages.append(PageText(page=i + 1, text=_normalise(text)))
    return pages


def _normalise(text: str) -> str:
    """Collapse hyphenated line breaks and run-on whitespace from PDF reflow."""
    text = text.replace("­", "")  # soft hyphen
    text = text.replace("-\n", "")  # word-broken hyphenation across lines
    return text.strip()
