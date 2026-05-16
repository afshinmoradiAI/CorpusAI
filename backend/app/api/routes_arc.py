"""ARC grant endpoints.

Routes:
- POST /api/arc/write   SSE stream of the ARC grant generation pipeline
"""

from __future__ import annotations

import json
from collections.abc import AsyncIterator

from fastapi import APIRouter, Depends, HTTPException, status
from sse_starlette.sse import EventSourceResponse

from app.core.security import current_user_id
from app.schemas.arc import ARCRequest
from app.services import ReferenceStore, get_reference_store
from app.workflows.arc import run_arc

router = APIRouter(prefix="/api/arc", tags=["arc"])


@router.post("/write")
async def write_arc(
    request: ARCRequest,
    store: ReferenceStore = Depends(get_reference_store),
    user_id: str | None = Depends(current_user_id),
) -> EventSourceResponse:
    if request.set_id and store.get_meta(request.set_id, user_id=user_id) is None:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, f"Unknown set_id: {request.set_id}"
        )
    return EventSourceResponse(_arc_event_stream(request, store, user_id))


async def _arc_event_stream(
    request: ARCRequest, store: ReferenceStore, user_id: str | None
) -> AsyncIterator[dict[str, str]]:
    try:
        async for event in run_arc(request, store=store, user_id=user_id):
            yield {"event": event.kind, "data": json.dumps(event.payload)}
    except Exception as exc:  # noqa: BLE001
        yield {
            "event": "error",
            "data": json.dumps({"message": str(exc), "type": exc.__class__.__name__}),
        }
