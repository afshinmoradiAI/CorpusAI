"""Explore endpoint: streams progress events over Server-Sent Events."""

from __future__ import annotations

import json
from collections.abc import AsyncIterator

from fastapi import APIRouter
from sse_starlette.sse import EventSourceResponse

from app.schemas.research import TopicRequest
from app.workflows.explore import run_explore

router = APIRouter(prefix="/api/research", tags=["research"])


@router.post("/explore")
async def explore(request: TopicRequest) -> EventSourceResponse:
    """Run the Explore pipeline and stream each step as an SSE event.

    Each event has `event: <kind>` and `data: <json payload>`. The terminal
    event is `completed` (with the full `ResearchOutput`) or `error`.
    """
    return EventSourceResponse(_event_stream(request))


async def _event_stream(request: TopicRequest) -> AsyncIterator[dict[str, str]]:
    try:
        async for event in run_explore(request):
            yield {"event": event.kind, "data": json.dumps(event.payload)}
    except Exception as exc:  # noqa: BLE001 — surface to client as an SSE event
        yield {
            "event": "error",
            "data": json.dumps({"message": str(exc), "type": exc.__class__.__name__}),
        }
