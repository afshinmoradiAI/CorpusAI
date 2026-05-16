"""Explore endpoint: streams progress events over Server-Sent Events."""

from __future__ import annotations

import json
from collections.abc import AsyncIterator

from fastapi import APIRouter, Depends
from sse_starlette.sse import EventSourceResponse

from app.core.security import current_user_id
from app.schemas.research import TopicRequest
from app.services import ReferenceStore, get_reference_store
from app.workflows.explore import run_explore

router = APIRouter(prefix="/api/research", tags=["research"])


@router.post("/explore")
async def explore(
    request: TopicRequest,
    store: ReferenceStore = Depends(get_reference_store),
    user_id: str | None = Depends(current_user_id),
) -> EventSourceResponse:
    """Run the Explore pipeline and stream each step as an SSE event.

    Each event has `event: <kind>` and `data: <json payload>`. The terminal
    event is `completed` (with the full `ResearchOutput`) or `error`.
    """
    bm25_index = None
    if request.set_id:
        bm25_index = store.get_index(request.set_id, user_id=user_id)

    return EventSourceResponse(_event_stream(request, bm25_index))


async def _event_stream(request: TopicRequest, bm25_index=None) -> AsyncIterator[dict[str, str]]:
    try:
        async for event in run_explore(request, bm25_index=bm25_index):
            yield {"event": event.kind, "data": json.dumps(event.payload)}
    except Exception as exc:  # noqa: BLE001 — surface to client as an SSE event
        yield {
            "event": "error",
            "data": json.dumps({"message": str(exc), "type": exc.__class__.__name__}),
        }
