"""Verify pdf_reader against PDFs generated in-process by reportlab."""

from __future__ import annotations

import io

import pytest
from reportlab.pdfgen import canvas  # type: ignore[import-untyped]

from app.services.pdf_reader import PDFReadError, read_pdf_bytes


def _make_pdf(pages_text: list[str]) -> bytes:
    buf = io.BytesIO()
    c = canvas.Canvas(buf)
    for text in pages_text:
        c.drawString(72, 720, text)
        c.showPage()
    c.save()
    return buf.getvalue()


def test_read_pdf_returns_one_pagetext_per_page() -> None:
    pdf = _make_pdf(["Hello biology", "Methods section start"])
    pages = read_pdf_bytes(pdf)
    assert [p.page for p in pages] == [1, 2]
    assert "Hello biology" in pages[0].text
    assert "Methods" in pages[1].text


def test_read_pdf_raises_on_garbage_bytes() -> None:
    with pytest.raises(PDFReadError):
        read_pdf_bytes(b"not a real pdf")
