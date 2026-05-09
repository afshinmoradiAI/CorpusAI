import io

import pytest
from reportlab.pdfgen import canvas  # type: ignore[import-untyped]

from app.services.reference_store import ReferenceStore


def _pdf(text: str) -> bytes:
    buf = io.BytesIO()
    c = canvas.Canvas(buf)
    c.drawString(72, 720, text)
    c.showPage()
    c.save()
    return buf.getvalue()


@pytest.mark.asyncio
async def test_create_set_indexes_and_returns_metadata() -> None:
    store = ReferenceStore()
    pdf_bytes = _pdf("CRISPR off-target effects in human T cells. " * 30)

    meta = await store.create_set([("paper1.pdf", pdf_bytes)])

    assert len(meta.documents) == 1
    assert meta.documents[0].filename == "paper1.pdf"
    assert meta.documents[0].page_count == 1

    fetched = store.get_meta(meta.set_id)
    assert fetched is not None
    assert fetched.set_id == meta.set_id

    index = store.get_index(meta.set_id)
    assert index is not None
    matches = index.search("crispr", k=3)
    assert matches and matches[0].chunk.ref_id == meta.documents[0].ref_id


def test_get_meta_returns_none_for_unknown_set() -> None:
    assert ReferenceStore().get_meta("does-not-exist") is None
