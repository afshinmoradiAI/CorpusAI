"""NHMRC grant endpoints.

Routes:
- POST /api/nhmrc/write   SSE stream of the NHMRC grant generation pipeline
"""

from __future__ import annotations

import json
from collections.abc import AsyncIterator

from fastapi import APIRouter, Depends, HTTPException, status
from sse_starlette.sse import EventSourceResponse

from app.core.security import current_user_id
from app.schemas.nhmrc import NHMRCRequest
from app.services import ReferenceStore, get_reference_store
from app.workflows.nhmrc import run_nhmrc

router = APIRouter(prefix="/api/nhmrc", tags=["nhmrc"])


@router.post("/write")
async def write_nhmrc(
    request: NHMRCRequest,
    store: ReferenceStore = Depends(get_reference_store),
    user_id: str | None = Depends(current_user_id),
) -> EventSourceResponse:
    if request.set_id and store.get_meta(request.set_id, user_id=user_id) is None:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, f"Unknown set_id: {request.set_id}"
        )
    return EventSourceResponse(_nhmrc_event_stream(request, store, user_id))


async def _nhmrc_event_stream(
    request: NHMRCRequest, store: ReferenceStore, user_id: str | None
) -> AsyncIterator[dict[str, str]]:
    try:
        async for event in run_nhmrc(request, store=store, user_id=user_id):
            yield {"event": event.kind, "data": json.dumps(event.payload)}
    except Exception as exc:  # noqa: BLE001
        yield {
            "event": "error",
            "data": json.dumps({"message": str(exc), "type": exc.__class__.__name__}),
        }
