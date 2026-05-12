import io
from pathlib import Path

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


def _store(tmp_path: Path) -> ReferenceStore:
    return ReferenceStore(tmp_path / "test.sqlite")


@pytest.mark.asyncio
async def test_create_set_indexes_and_returns_metadata(tmp_path: Path) -> None:
    store = _store(tmp_path)
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


def test_get_meta_returns_none_for_unknown_set(tmp_path: Path) -> None:
    assert _store(tmp_path).get_meta("does-not-exist") is None


@pytest.mark.asyncio
async def test_user_scoping_isolates_sets(tmp_path: Path) -> None:
    store = _store(tmp_path)
    pdf_bytes = _pdf("Some content text. " * 30)

    meta_alice = await store.create_set([("a.pdf", pdf_bytes)], user_id="alice")
    meta_bob = await store.create_set([("b.pdf", pdf_bytes)], user_id="bob")
    meta_anon = await store.create_set([("c.pdf", pdf_bytes)])

    alice_sets = store.list_sets(user_id="alice")
    assert meta_alice.set_id in alice_sets
    assert meta_anon.set_id in alice_sets
    assert meta_bob.set_id not in alice_sets

    assert store.get_meta(meta_alice.set_id, user_id="bob") is None
    assert store.get_index(meta_alice.set_id, user_id="bob") is None

    assert store.get_meta(meta_anon.set_id, user_id="bob") is not None


@pytest.mark.asyncio
async def test_persistence_across_instances(tmp_path: Path) -> None:
    pdf_bytes = _pdf("Persisted content. " * 30)

    store1 = _store(tmp_path)
    meta = await store1.create_set([("p.pdf", pdf_bytes)], user_id="alice")

    store2 = ReferenceStore(tmp_path / "test.sqlite")
    fetched = store2.get_meta(meta.set_id, user_id="alice")
    assert fetched is not None
    assert fetched.documents[0].filename == "p.pdf"
