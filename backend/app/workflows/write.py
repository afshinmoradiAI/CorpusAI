"""Write workflow: PDFs → drafted sections → assembled paper → 3-way peer review.

Flow:
1. Look up the user's reference set (Phase 3 store).
2. For each requested section in canonical order:
   a. Build a section-specific retrieval query.
   b. Pull top-k chunks from the BM25 index.
   c. Run the matching writer agent (passing already-written sections).
3. Run the ReferenceFormatter to produce a citation list.
4. Assemble final markdown (reference markers `[ref=ID]` → `[N]`).
5. Run BiologyReviewer, StatisticsReviewer, GapReviewer in parallel.
6. Run ReviewSynthesiser on the merged feedback.
7. Yield events at every step; final event carries the WriteResult.
"""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from dataclasses import dataclass
from typing import Any, Literal

from app.agents import (
    AbstractWriter,
    BiologyReviewer,
    DiscussionWriter,
    GapReviewer,
    IntroductionWriter,
    MethodsWriter,
    ReferenceFormatter,
    ResultsWriter,
    ReviewSynthesiser,
    StatisticsReviewer,
)
from app.agents.section_writers import _SectionWriter
from app.schemas.paper import (
    CANONICAL_ORDER,
    FormattedReference,
    PaperDraft,
    ReferenceFormatterInput,
    ReviewerInput,
    ReviewReport,
    ReviewSynthesisInput,
    SectionName,
    WriteRequest,
    WriteResult,
    WriterInput,
)
from app.schemas.papers import Chunk
from app.services import ReferenceStore, get_reference_store

EventKind = Literal[
    "started",
    "section_started",
    "section_completed",
    "references_formatted",
    "paper_assembled",
    "review_started",
    "review_completed",
    "completed",
    "error",
]


@dataclass
class WriteEvent:
    kind: EventKind
    payload: dict[str, Any]


_WRITERS: dict[SectionName, type[_SectionWriter]] = {
    SectionName.ABSTRACT: AbstractWriter,
    SectionName.INTRODUCTION: IntroductionWriter,
    SectionName.METHODS: MethodsWriter,
    SectionName.RESULTS: ResultsWriter,
    SectionName.DISCUSSION: DiscussionWriter,
}

_SECTION_QUERIES: dict[SectionName, str] = {
    SectionName.ABSTRACT: "abstract summary background aim findings",
    SectionName.INTRODUCTION: "background motivation prior work hypothesis",
    SectionName.METHODS: "methods protocol assay materials statistical analysis",
    SectionName.RESULTS: "results findings outcome measurement effect",
    SectionName.DISCUSSION: "discussion implication limitation interpretation",
}

_TOP_K_PER_SECTION = 6


async def run_write(
    request: WriteRequest,
    *,
    store: ReferenceStore | None = None,
    skip_review: bool = False,
) -> AsyncIterator[WriteEvent]:
    store = store or get_reference_store()
    meta = store.get_meta(request.set_id)
    index = store.get_index(request.set_id)
    if meta is None or index is None:
        yield WriteEvent("error", {"message": f"Unknown set_id: {request.set_id}"})
        return

    yield WriteEvent("started", {"topic": request.topic, "set_id": request.set_id})

    selected = {s for s in request.sections}
    drafted: dict[SectionName, str] = {}

    for section in CANONICAL_ORDER:
        if section not in selected:
            continue
        yield WriteEvent("section_started", {"section": section.value})

        query = f"{request.topic} {_SECTION_QUERIES[section]}"
        chunks: list[Chunk] = [m.chunk for m in index.search(query, k=_TOP_K_PER_SECTION)]

        writer = _WRITERS[section]()
        draft = await writer.run(
            WriterInput(
                topic=request.topic,
                section=section,
                chunks=chunks,
                other_sections={k.value: v for k, v in drafted.items()},
                user_results=request.user_results if section == SectionName.RESULTS else None,
                notes=request.notes,
            )
        )
        drafted[section] = draft.content
        yield WriteEvent(
            "section_completed",
            {"section": section.value, "content": draft.content},
        )

    sample_chunks = _sample_chunks_per_ref(meta, index)
    references = await ReferenceFormatter().run(
        ReferenceFormatterInput(documents=meta.documents, sample_chunks_by_ref=sample_chunks)
    )
    yield WriteEvent(
        "references_formatted",
        {"count": len(references.references)},
    )

    paper = _assemble_paper(
        topic=request.topic,
        drafted=drafted,
        references=references.references,
    )
    yield WriteEvent("paper_assembled", {"markdown": paper.markdown})

    review: ReviewReport | None = None
    if not skip_review:
        yield WriteEvent("review_started", {})
        review = await _run_reviews(request.topic, paper.markdown)
        yield WriteEvent("review_completed", review.model_dump())

    yield WriteEvent(
        "completed",
        WriteResult(paper=paper, review=review).model_dump(),
    )


async def _run_reviews(topic: str, markdown: str) -> ReviewReport:
    reviewer_input = ReviewerInput(topic=topic, paper_markdown=markdown)
    biology, statistics, gap = await asyncio.gather(
        BiologyReviewer().run(reviewer_input),
        StatisticsReviewer().run(reviewer_input),
        GapReviewer().run(reviewer_input),
    )
    synthesis = await ReviewSynthesiser().run(
        ReviewSynthesisInput(
            topic=topic, biology=biology, statistics=statistics, gap=gap
        )
    )
    return ReviewReport(
        biology=biology, statistics=statistics, gap=gap, synthesis=synthesis
    )


def _sample_chunks_per_ref(meta, index) -> dict[str, list[str]]:
    out: dict[str, list[str]] = {}
    for doc in meta.documents:
        out[doc.ref_id] = [
            c.text[:300] for c in index.chunks if c.ref_id == doc.ref_id
        ][:2]
    return out


def _assemble_paper(
    *,
    topic: str,
    drafted: dict[SectionName, str],
    references: list[FormattedReference],
) -> PaperDraft:
    """Assemble final markdown — replace [ref=ID] markers with [N] citations."""
    ref_index: dict[str, int] = {r.ref_id: i + 1 for i, r in enumerate(references)}

    sections_out: dict[str, str] = {}
    parts: list[str] = [f"# {topic}", ""]

    display_order = [
        SectionName.ABSTRACT,
        SectionName.INTRODUCTION,
        SectionName.METHODS,
        SectionName.RESULTS,
        SectionName.DISCUSSION,
    ]
    for section in display_order:
        if section not in drafted:
            continue
        body = _replace_refs(drafted[section], ref_index)
        sections_out[section.value] = body
        parts.append(f"## {section.value.title()}")
        parts.append("")
        parts.append(body)
        parts.append("")

    if references:
        parts.append("## References")
        parts.append("")
        for i, ref in enumerate(references, start=1):
            parts.append(f"[{i}] {ref.citation}")
        parts.append("")

    return PaperDraft(
        topic=topic,
        sections=sections_out,
        references=references,
        markdown="\n".join(parts).strip() + "\n",
    )


def _replace_refs(text: str, ref_index: dict[str, int]) -> str:
    import re

    def sub(match: re.Match[str]) -> str:
        ref_id = match.group(1)
        n = ref_index.get(ref_id)
        return f"[{n}]" if n else "[?]"

    return re.sub(r"\[ref=([a-zA-Z0-9\-]+)\]", sub, text)
