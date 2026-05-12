"""Tests for the DELETE /api/paper/refs/{set_id} endpoint."""

from __future__ import annotations

import io
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from reportlab.pdfgen import canvas  # type: ignore[import-untyped]

import app.core.config as cfg
from app.services.reference_store import (
    ReferenceStore,
    reset_reference_store,
)


def _pdf(text: str) -> bytes:
    buf = io.BytesIO()
    c = canvas.Canvas(buf)
    c.drawString(72, 720, text)
    c.showPage()
    c.save()
    return buf.getvalue()


@pytest.fixture
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    cfg.get_settings.cache_clear()
    reset_reference_store()
    from app.main import app

    return TestClient(app)


def test_delete_set_removes_data(client: TestClient) -> None:
    pdf = _pdf("Some content to chunk. " * 20)
    upload = client.post(
        "/api/paper/upload-refs",
        files=[("files", ("p.pdf", pdf, "application/pdf"))],
    )
    assert upload.status_code == 200
    set_id = upload.json()["set_id"]

    # Pre-delete: visible
    assert client.get(f"/api/paper/refs/{set_id}").status_code == 200

    # Delete succeeds
    res = client.delete(f"/api/paper/refs/{set_id}")
    assert res.status_code == 204

    # Post-delete: gone
    assert client.get(f"/api/paper/refs/{set_id}").status_code == 404
    # Second delete: 404 not 500
    assert client.delete(f"/api/paper/refs/{set_id}").status_code == 404


def test_delete_respects_user_scoping(tmp_path: Path) -> None:
    store = ReferenceStore(tmp_path / "test.sqlite")
    pdf = _pdf("Some content. " * 20)

    import asyncio

    meta = asyncio.run(store.create_set([("a.pdf", pdf)], user_id="alice"))

    # Bob cannot delete Alice's set
    from app.services.reference_store import ReferenceStoreError

    with pytest.raises(ReferenceStoreError):
        store.delete_set(meta.set_id, user_id="bob")

    # Alice can
    assert store.delete_set(meta.set_id, user_id="alice") is True
    assert store.get_meta(meta.set_id, user_id="alice") is None
