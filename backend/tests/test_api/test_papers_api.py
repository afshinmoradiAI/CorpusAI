"""End-to-end test of the paper upload + search API."""

from __future__ import annotations

import io

from fastapi.testclient import TestClient
from reportlab.pdfgen import canvas  # type: ignore[import-untyped]

from app.main import app


def _pdf(text: str) -> bytes:
    buf = io.BytesIO()
    c = canvas.Canvas(buf)
    c.drawString(72, 720, text)
    c.showPage()
    c.save()
    return buf.getvalue()


def test_upload_then_search_roundtrip() -> None:
    client = TestClient(app)
    pdf = _pdf("CRISPR off-target effects in primary human T cells. " * 40)

    upload = client.post(
        "/api/paper/upload-refs",
        files=[("files", ("p1.pdf", pdf, "application/pdf"))],
    )
    assert upload.status_code == 200, upload.text
    body = upload.json()
    set_id = body["set_id"]
    assert len(body["documents"]) == 1

    search = client.post(
        f"/api/paper/refs/{set_id}/search",
        json={"query": "crispr", "k": 3},
    )
    assert search.status_code == 200
    matches = search.json()
    assert matches
    # BM25 IDF can be negative on a single-document corpus; just verify
    # the chunk anchored to the uploaded ref came back.
    assert matches[0]["chunk"]["ref_id"] == body["documents"][0]["ref_id"]


def test_upload_rejects_non_pdf() -> None:
    client = TestClient(app)
    bad = client.post(
        "/api/paper/upload-refs",
        files=[("files", ("notes.txt", b"hello", "text/plain"))],
    )
    assert bad.status_code == 400


def test_search_unknown_set_returns_404() -> None:
    client = TestClient(app)
    response = client.post(
        "/api/paper/refs/does-not-exist/search",
        json={"query": "anything", "k": 3},
    )
    assert response.status_code == 404
