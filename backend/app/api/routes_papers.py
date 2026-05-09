"""Paper endpoints — ingestion (Phase 3) + writing (Phase 4).

Routes:
- POST /api/paper/upload-refs            multipart upload, parses + indexes PDFs
- GET  /api/paper/refs/{set_id}          fetch metadata for an uploaded set
- POST /api/paper/refs/{set_id}/search   debug helper for the BM25 index
- POST /api/paper/write                  SSE stream of the write pipeline
"""

from __future__ import annotations

import json
from collections.abc import AsyncIterator

from fastapi import APIRouter, Depends, HTTPException, UploadFile, status
from fastapi.responses import Response
from pydantic import BaseModel, Field
from sse_starlette.sse import EventSourceResponse

from app.schemas.paper import WriteRequest
from app.schemas.papers import ChunkMatch, RefSet, SearchRequest
from app.services import ReferenceStore, get_reference_store
from app.services.docx_export import paper_to_docx
from app.services.pdf_reader import PDFReadError
from app.workflows.write import run_write


class DocxExportRequest(BaseModel):
    markdown: str = Field(min_length=1)
    filename: str = Field(default="paper.docx")

router = APIRouter(prefix="/api/paper", tags=["paper"])

_MAX_FILES = 30
_MAX_BYTES_PER_FILE = 25 * 1024 * 1024  # 25 MB


@router.post("/upload-refs", response_model=RefSet)
async def upload_refs(
    files: list[UploadFile],
    store: ReferenceStore = Depends(get_reference_store),
) -> RefSet:
    if not files:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "No files uploaded.")
    if len(files) > _MAX_FILES:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            f"At most {_MAX_FILES} files per upload.",
        )

    payload: list[tuple[str, bytes]] = []
    for f in files:
        if not (f.filename or "").lower().endswith(".pdf"):
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                f"Only .pdf files accepted; got {f.filename!r}.",
            )
        data = await f.read()
        if len(data) > _MAX_BYTES_PER_FILE:
            raise HTTPException(
                status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                f"{f.filename} exceeds {_MAX_BYTES_PER_FILE // (1024 * 1024)} MB.",
            )
        payload.append((f.filename or "unknown.pdf", data))

    try:
        return await store.create_set(payload)
    except PDFReadError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc)) from exc


@router.get("/refs/{set_id}", response_model=RefSet)
async def get_ref_set(
    set_id: str,
    store: ReferenceStore = Depends(get_reference_store),
) -> RefSet:
    meta = store.get_meta(set_id)
    if meta is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Unknown set_id: {set_id}")
    return meta


@router.post("/refs/{set_id}/search", response_model=list[ChunkMatch])
async def search_chunks(
    set_id: str,
    request: SearchRequest,
    store: ReferenceStore = Depends(get_reference_store),
) -> list[ChunkMatch]:
    index = store.get_index(set_id)
    if index is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Unknown set_id: {set_id}")
    return index.search(request.query, k=request.k)


@router.post("/write")
async def write_paper(
    request: WriteRequest,
    store: ReferenceStore = Depends(get_reference_store),
) -> EventSourceResponse:
    """Stream the Write pipeline as SSE events.

    The set_id must come from a prior `/upload-refs` call. Each section in
    `request.sections` produces a `section_started` + `section_completed`
    pair; the terminal event is `completed` (with the full WriteResult).
    """
    if store.get_meta(request.set_id) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Unknown set_id: {request.set_id}")
    return EventSourceResponse(_write_event_stream(request, store))


async def _write_event_stream(
    request: WriteRequest, store: ReferenceStore
) -> AsyncIterator[dict[str, str]]:
    try:
        async for event in run_write(request, store=store):
            yield {"event": event.kind, "data": json.dumps(event.payload)}
    except Exception as exc:  # noqa: BLE001
        yield {
            "event": "error",
            "data": json.dumps({"message": str(exc), "type": exc.__class__.__name__}),
        }


@router.post("/export/docx")
async def export_docx(request: DocxExportRequest) -> Response:
    """Convert assembled paper markdown into a .docx download."""
    body = paper_to_docx(request.markdown)
    safe_name = request.filename if request.filename.endswith(".docx") else f"{request.filename}.docx"
    return Response(
        content=body,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": f'attachment; filename="{safe_name}"'},
    )
