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
from app.schemas.research import (
    DiscussionWriterInput,
    GapFinderInput,
    IdeaGeneratorInput,
    MethodDesignerInput,
    PaperSummariserInput,
    PaperSummary,
    RawPaper,
    ResearchOutput,
    TopicAnalysis,
    TopicRequest,
)
from app.services import search_papers

EventKind = Literal[
    "started",
    "topic_analysed",
    "papers_found",
    "papers_summarised",
    "gap_found",
    "idea_generated",
    "method_designed",
    "discussion_written",
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
