"""Async client for Semantic Scholar's Graph API.

Free, no API key required for moderate use. We use the /paper/search
endpoint and project a small set of fields onto our `RawPaper` model.

Docs: https://api.semanticscholar.org/api-docs/graph
"""

from __future__ import annotations

from typing import Any

import httpx

from app.schemas.research import RawPaper

_BASE_URL = "https://api.semanticscholar.org/graph/v1"
_FIELDS = "title,abstract,year,authors.name,venue,citationCount,externalIds,url"


class SemanticScholarError(RuntimeError):
    """Wraps any non-recoverable failure from the upstream API."""


async def search_papers(
    query: str,
    *,
    limit: int = 10,
    min_citations: int | None = None,
    timeout: float = 20.0,
) -> list[RawPaper]:
    """Run a full-text search and return at most `limit` papers with abstracts."""
    params: dict[str, Any] = {
        "query": query,
        "limit": min(max(limit, 1), 50),
        "fields": _FIELDS,
    }
    async with httpx.AsyncClient(timeout=timeout) as client:
        try:
            response = await client.get(f"{_BASE_URL}/paper/search", params=params)
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise SemanticScholarError(f"Semantic Scholar request failed: {exc}") from exc

    data = response.json().get("data", [])
    papers = [_to_raw_paper(item) for item in data]
    papers = [p for p in papers if p.abstract]
    if min_citations is not None:
        papers = [p for p in papers if (p.citation_count or 0) >= min_citations]
    return papers[:limit]


def _to_raw_paper(item: dict[str, Any]) -> RawPaper:
    authors = [a.get("name", "") for a in item.get("authors") or [] if a.get("name")]
    return RawPaper(
        source_id=item.get("paperId") or "",
        title=item.get("title") or "",
        abstract=item.get("abstract"),
        year=item.get("year"),
        authors=authors,
        venue=item.get("venue") or None,
        citation_count=item.get("citationCount"),
        url=item.get("url"),
    )
