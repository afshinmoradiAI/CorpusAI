"""Paper endpoints — ingestion + writing.

Routes:
- POST /api/paper/upload-refs            multipart upload, parses + indexes PDFs
- GET  /api/paper/refs                   list set_ids owned by the caller
- GET  /api/paper/refs/{set_id}          fetch metadata for an uploaded set
- POST /api/paper/refs/{set_id}/search   debug helper for the BM25 index
- POST /api/paper/write                  SSE stream of the write pipeline
- POST /api/paper/export/docx            convert markdown to .docx download
"""

from __future__ import annotations

import json
from collections.abc import AsyncIterator

from fastapi import APIRouter, Depends, HTTPException, UploadFile, status
from fastapi.responses import Response
from pydantic import BaseModel, Field
from sse_starlette.sse import EventSourceResponse

from app.core.security import current_user_id
from app.schemas.paper import WriteRequest
from app.schemas.papers import ChunkMatch, RefSet, SearchRequest
from app.services import ReferenceStore, get_reference_store
from app.services.docx_export import paper_to_docx
from app.services.pdf_reader import PDFReadError
from app.services.reference_store import ReferenceStoreError
from app.workflows.write import run_write


class DocxExportRequest(BaseModel):
    markdown: str = Field(min_length=1)
    filename: str = Field(default="paper.docx")


class RefSetSummary(BaseModel):
    set_ids: list[str]


router = APIRouter(prefix="/api/paper", tags=["paper"])

_MAX_FILES = 30
_MAX_BYTES_PER_FILE = 25 * 1024 * 1024  # 25 MB


@router.post("/upload-refs", response_model=RefSet)
async def upload_refs(
    files: list[UploadFile],
    store: ReferenceStore = Depends(get_reference_store),
    user_id: str | None = Depends(current_user_id),
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
        return await store.create_set(payload, user_id=user_id)
    except PDFReadError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc)) from exc


@router.get("/refs", response_model=RefSetSummary)
async def list_refs(
    store: ReferenceStore = Depends(get_reference_store),
    user_id: str | None = Depends(current_user_id),
) -> RefSetSummary:
    return RefSetSummary(set_ids=store.list_sets(user_id=user_id))


@router.get("/refs/{set_id}", response_model=RefSet)
async def get_ref_set(
    set_id: str,
    store: ReferenceStore = Depends(get_reference_store),
    user_id: str | None = Depends(current_user_id),
) -> RefSet:
    meta = store.get_meta(set_id, user_id=user_id)
    if meta is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Unknown set_id: {set_id}")
    return meta


@router.delete("/refs/{set_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_ref_set(
    set_id: str,
    store: ReferenceStore = Depends(get_reference_store),
    user_id: str | None = Depends(current_user_id),
) -> Response:
    try:
        removed = store.delete_set(set_id, user_id=user_id)
    except ReferenceStoreError as exc:
        raise HTTPException(status.HTTP_403_FORBIDDEN, str(exc)) from exc
    if not removed:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Unknown set_id: {set_id}")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/refs/{set_id}/search", response_model=list[ChunkMatch])
async def search_chunks(
    set_id: str,
    request: SearchRequest,
    store: ReferenceStore = Depends(get_reference_store),
    user_id: str | None = Depends(current_user_id),
) -> list[ChunkMatch]:
    index = store.get_index(set_id, user_id=user_id)
    if index is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Unknown set_id: {set_id}")
    return index.search(request.query, k=request.k)


@router.post("/write")
async def write_paper(
    request: WriteRequest,
    store: ReferenceStore = Depends(get_reference_store),
    user_id: str | None = Depends(current_user_id),
) -> EventSourceResponse:
    if store.get_meta(request.set_id, user_id=user_id) is None:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, f"Unknown set_id: {request.set_id}"
        )
    return EventSourceResponse(_write_event_stream(request, store, user_id))


async def _write_event_stream(
    request: WriteRequest, store: ReferenceStore, user_id: str | None
) -> AsyncIterator[dict[str, str]]:
    try:
        async for event in run_write(request, store=store, user_id=user_id):
            yield {"event": event.kind, "data": json.dumps(event.payload)}
    except Exception as exc:  # noqa: BLE001
        yield {
            "event": "error",
            "data": json.dumps({"message": str(exc), "type": exc.__class__.__name__}),
        }


@router.post("/export/docx")
async def export_docx(request: DocxExportRequest) -> Response:
    body = paper_to_docx(request.markdown)
    safe_name = (
        request.filename if request.filename.endswith(".docx")
        else f"{request.filename}.docx"
    )
    return Response(
        content=body,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": f'attachment; filename="{safe_name}"'},
    )
