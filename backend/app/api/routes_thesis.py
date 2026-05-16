"""Thesis endpoints.

Two routers because the figure GET must be reachable by the browser's
`<img>` tag, which cannot attach custom headers like `X-API-Key`.

Authenticated (`router`):
- POST /api/thesis/upload-figure   single-image upload, returns figure_id
- POST /api/thesis/write           SSE stream of the Thesis generation pipeline

Public (`public_router`):
- GET  /api/thesis/figure/{id}     stream a stored figure
  Security relies on figure_id being a 128-bit UUID4 (unguessable).
"""

from __future__ import annotations

import json
import mimetypes
from collections.abc import AsyncIterator

from fastapi import APIRouter, Depends, HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from sse_starlette.sse import EventSourceResponse

from app.core.security import current_user_id
from app.schemas.thesis import ThesisRequest, UploadedFigure
from app.services import ReferenceStore, get_reference_store
from app.services.figure_store import FigureStoreError, path_for, save_figure
from app.workflows.thesis import run_thesis

router = APIRouter(prefix="/api/thesis", tags=["thesis"])
public_router = APIRouter(prefix="/api/thesis", tags=["thesis"])

_MAX_FIGURE_BYTES = 10 * 1024 * 1024  # 10 MB


@router.post("/upload-figure", response_model=UploadedFigure)
async def upload_figure(file: UploadFile) -> UploadedFigure:
    if not file.filename:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Missing filename.")
    data = await file.read()
    if not data:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Empty file.")
    if len(data) > _MAX_FIGURE_BYTES:
        raise HTTPException(
            status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            f"Figure exceeds {_MAX_FIGURE_BYTES // (1024 * 1024)} MB.",
        )
    try:
        figure_id, _ = save_figure(file.filename, data)
    except FigureStoreError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc)) from exc
    return UploadedFigure(figure_id=figure_id, filename=file.filename)


@public_router.get("/figure/{figure_id}")
async def get_figure(figure_id: str) -> FileResponse:
    path = path_for(figure_id)
    if path is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Figure not found.")
    media_type, _ = mimetypes.guess_type(path.name)
    return FileResponse(path, media_type=media_type or "application/octet-stream")


@router.post("/write")
async def write_thesis(
    request: ThesisRequest,
    store: ReferenceStore = Depends(get_reference_store),
    user_id: str | None = Depends(current_user_id),
) -> EventSourceResponse:
    for idx, ch in enumerate(request.chapters, start=1):
        if ch.set_id and store.get_meta(ch.set_id, user_id=user_id) is None:
            raise HTTPException(
                status.HTTP_404_NOT_FOUND,
                f"Unknown set_id for chapter {idx}: {ch.set_id}",
            )
    return EventSourceResponse(_thesis_event_stream(request, store, user_id))


async def _thesis_event_stream(
    request: ThesisRequest, store: ReferenceStore, user_id: str | None
) -> AsyncIterator[dict[str, str]]:
    try:
        async for event in run_thesis(request, store=store, user_id=user_id):
            yield {"event": event.kind, "data": json.dumps(event.payload)}
    except Exception as exc:  # noqa: BLE001
        yield {
            "event": "error",
            "data": json.dumps({"message": str(exc), "type": exc.__class__.__name__}),
        }
