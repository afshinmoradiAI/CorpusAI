"""MCP server exposing CorpusAI's paper services to external MCP clients.

Run with:
    uv run python -m app.mcp_server

By default it speaks the streamable HTTP transport on port 8765. Point
any MCP client (Claude Desktop, Claude Code, your own PydanticAI agents)
at `http://localhost:8765/mcp` to use these tools.

Authentication
--------------
If `APP_API_KEY` is set in the environment, every request must include
header `X-API-Key: <key>`. Empty key = dev mode (no auth — same convention
as the FastAPI layer).

Tools exposed:
- search_external_papers: query Semantic Scholar
- list_ref_sets:          enumerate uploaded sets for a user
- get_ref_set:            fetch metadata for a set
- search_chunks:          BM25 search inside a set
"""

from __future__ import annotations

from typing import Any

from mcp.server.fastmcp import FastMCP
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from app.core.config import get_settings
from app.core.logging import configure_logging, get_logger
from app.services import get_reference_store, search_papers

configure_logging()
_log = get_logger(__name__)

mcp = FastMCP("corpusai")


class APIKeyMiddleware(BaseHTTPMiddleware):
    """Reject requests without a valid X-API-Key when APP_API_KEY is configured."""

    async def dispatch(self, request: Request, call_next):  # type: ignore[no-untyped-def]
        expected = get_settings().app_api_key
        if expected:
            provided = request.headers.get("X-API-Key")
            if not provided or provided != expected:
                _log.warning(
                    "mcp_auth_rejected",
                    path=request.url.path,
                    ip=request.client.host if request.client else "?",
                )
                return JSONResponse(
                    status_code=401,
                    content={
                        "type": "about:blank",
                        "title": "Unauthorized",
                        "status": 401,
                        "detail": "Invalid or missing API key",
                    },
                    media_type="application/problem+json",
                )
        return await call_next(request)


@mcp.tool()
async def search_external_papers(
    query: str, limit: int = 8
) -> list[dict[str, Any]]:
    """Search Semantic Scholar for papers matching the query.

    Returns a list of {source_id, title, abstract, year, authors, venue, url}.
    """
    papers = await search_papers(query, limit=limit)
    return [p.model_dump() for p in papers]


@mcp.tool()
def list_ref_sets(user_id: str | None = None) -> list[str]:
    """List set_ids owned by `user_id` (plus anonymous sets). None = all anon."""
    return get_reference_store().list_sets(user_id=user_id)


@mcp.tool()
def get_ref_set(set_id: str, user_id: str | None = None) -> dict[str, Any] | None:
    """Fetch metadata (documents + page counts) for a reference set."""
    meta = get_reference_store().get_meta(set_id, user_id=user_id)
    return meta.model_dump() if meta else None


@mcp.tool()
def search_chunks(
    set_id: str, query: str, k: int = 5, user_id: str | None = None
) -> list[dict[str, Any]]:
    """BM25 search over chunks within a specific reference set."""
    index = get_reference_store().get_index(set_id, user_id=user_id)
    if index is None:
        return []
    return [m.model_dump() for m in index.search(query, k=k)]


def main() -> None:
    settings = get_settings()
    _ = settings
    # FastMCP exposes a Starlette app under .streamable_http_app(); we add
    # the auth middleware before handing it to uvicorn.
    app = mcp.streamable_http_app()
    app.add_middleware(APIKeyMiddleware)
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8765)


if __name__ == "__main__":
    main()
