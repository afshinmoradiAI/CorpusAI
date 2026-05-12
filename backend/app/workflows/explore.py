"""Explore workflow: topic -> literature -> summaries -> gap -> idea -> method -> discussion.

The orchestrator is a single async generator. Each step yields a typed
`ExploreEvent` so the API layer can stream progress over SSE without
caring how the pipeline is implemented internally.

Per CLAUDE.md, agents do not call each other directly — they are all
invoked from this orchestrator.
"""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator, Iterable
from dataclasses import dataclass
from typing import Any, Literal

from app.agents import (
    ExploreDiscussionWriter,
    GapFinder,
    IdeaGenerator,
    MethodDesigner,
    PaperSummariser,
    TopicAnalyser,
)
from app.core.cache import LRUCache, hash_payload
from app.core.config import get_settings
from app.core.logging import get_logger
from app.core.usage import SpendCapExceeded, usage_scope
from app.schemas.research import (
    DiscussionWriterInput,
    GapFinderInput,
    IdeaGeneratorInput,
    MethodDesignerInput,
    PaperSummariserInput,
    PaperSummary,
    RawPaper,
    ResearchOutput,
    TopicRequest,
)
from app.services import search_papers

_log = get_logger(__name__)
_result_cache: LRUCache[ResearchOutput] = LRUCache(
    get_settings().result_cache_size
)

EventKind = Literal[
    "started",
    "topic_analysed",
    "papers_found",
    "papers_summarised",
    "gap_found",
    "idea_generated",
    "method_designed",
    "discussion_written",
    "usage",
    "completed",
    "error",
]


@dataclass
class ExploreEvent:
    kind: EventKind
    payload: dict[str, Any]


SearchFn = Any  # accepts the search_papers callable, parameterised for tests


async def run_explore(
    request: TopicRequest,
    *,
    paper_limit: int = 8,
    search_fn: SearchFn = search_papers,
) -> AsyncIterator[ExploreEvent]:
    """Drive the full Explore pipeline, yielding one event per step."""
    yield ExploreEvent("started", {"topic": request.topic})

    cache_key = hash_payload(
        {"kind": "explore", "request": request.model_dump(), "paper_limit": paper_limit}
    )
    cached = _result_cache.get(cache_key)
    if cached is not None:
        _log.info("explore_cache_hit", topic=request.topic)
        yield ExploreEvent("completed", cached.model_dump())
        return

    settings = get_settings()
    try:
        with usage_scope(settings.max_tokens_per_request) as scope:
            async for event in _run_explore_inner(
                request, paper_limit=paper_limit, search_fn=search_fn
            ):
                if event.kind == "completed":
                    _result_cache.put(
                        cache_key, ResearchOutput.model_validate(event.payload)
                    )
                    yield ExploreEvent("usage", scope.summary())
                yield event
            _log.info(
                "explore_completed",
                topic=request.topic,
                input_tokens=scope.input_tokens,
                output_tokens=scope.output_tokens,
                cache_read=scope.cache_read_tokens,
                requests=scope.requests,
                estimated_cost_usd=scope.estimated_cost_usd(),
            )
    except SpendCapExceeded as exc:
        yield ExploreEvent("error", {"message": str(exc), "type": "SpendCapExceeded"})


async def _run_explore_inner(
    request: TopicRequest,
    *,
    paper_limit: int,
    search_fn: SearchFn,
) -> AsyncIterator[ExploreEvent]:
    analysis = await TopicAnalyser().run(request)
    yield ExploreEvent(
        "topic_analysed",
        {
            "canonical_topic": analysis.canonical_topic,
            "keywords": analysis.keywords,
            "sub_domains": analysis.sub_domains,
        },
    )

    query = " ".join(analysis.keywords[:6])
    raw_papers: list[RawPaper] = await search_fn(query, limit=paper_limit)
    yield ExploreEvent(
        "papers_found",
        {"count": len(raw_papers), "titles": [p.title for p in raw_papers]},
    )

    if not raw_papers:
        yield ExploreEvent("error", {"message": "No papers with abstracts found."})
        return

    summaries = await _summarise_papers(raw_papers)
    yield ExploreEvent("papers_summarised", {"count": len(summaries)})

    gap = await GapFinder().run(
        GapFinderInput(topic=analysis.canonical_topic, summaries=summaries)
    )
    yield ExploreEvent(
        "gap_found",
        {"description": gap.description, "evidence": gap.evidence},
    )

    idea = await IdeaGenerator().run(
        IdeaGeneratorInput(
            topic=analysis.canonical_topic, gap=gap, summaries=summaries
        )
    )
    yield ExploreEvent("idea_generated", {"idea": idea.idea})

    method = await MethodDesigner().run(
        MethodDesignerInput(
            topic=analysis.canonical_topic, gap=gap, idea=idea.idea
        )
    )
    yield ExploreEvent("method_designed", {"method": method.method})

    discussion = await ExploreDiscussionWriter().run(
        DiscussionWriterInput(
            topic=analysis.canonical_topic,
            gap=gap,
            idea=idea.idea,
            method=method.method,
        )
    )
    yield ExploreEvent("discussion_written", {"discussion": discussion.discussion})

    output = ResearchOutput(
        topic=analysis.canonical_topic,
        gap=gap,
        idea=idea.idea,
        method=method.method,
        discussion=discussion.discussion,
        references=summaries,
    )
    yield ExploreEvent("completed", output.model_dump())


async def _summarise_papers(papers: Iterable[RawPaper]) -> list[PaperSummary]:
    """Summarise papers concurrently. Skips any that fail rather than aborting."""
    summariser = PaperSummariser()

    async def one(paper: RawPaper) -> PaperSummary | None:
        try:
            return await summariser.run(PaperSummariserInput(paper=paper))
        except Exception:
            return None

    results = await asyncio.gather(*(one(p) for p in papers))
    return [r for r in results if r is not None]
