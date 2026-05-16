"""ARC grant workflow.

Generates the standard ARC grant sections in canonical order:
    Significance -> Innovation -> Aims -> Approach & Methodology ->
    National Benefit -> Opening Statement (written last, placed first)

If the user supplies a `set_id` (uploaded PDFs), each section is grounded
in BM25-retrieved excerpts from that reference set, and a reference list
is formatted at the end. If no PDFs are supplied, the workflow runs
without retrieval and emits no references.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from dataclasses import dataclass
from typing import Any, Literal

from app.agents import (
    ARCAimsWriter,
    ARCApproachWriter,
    ARCInnovationWriter,
    ARCNationalBenefitWriter,
    ARCOpeningWriter,
    ARCSignificanceWriter,
    ReferenceFormatter,
)
from app.agents.arc_writers import _ARCWriter
from app.core.cache import LRUCache, hash_payload
from app.core.config import get_settings
from app.core.logging import get_logger
from app.core.usage import SpendCapExceeded, usage_scope
from app.schemas.arc import (
    CANONICAL_ARC_ORDER,
    ARCGrantDraft,
    ARCRequest,
    ARCResult,
    ARCSectionName,
    ARCWriterInput,
)
from app.schemas.paper import FormattedReference, ReferenceFormatterInput
from app.schemas.papers import Chunk
from app.services import ReferenceStore, get_reference_store

EventKind = Literal[
    "started",
    "section_started",
    "section_completed",
    "references_formatted",
    "grant_assembled",
    "usage",
    "completed",
    "error",
]


@dataclass
class ARCEvent:
    kind: EventKind
    payload: dict[str, Any]


_WRITERS: dict[ARCSectionName, type[_ARCWriter]] = {
    ARCSectionName.OPENING: ARCOpeningWriter,
    ARCSectionName.AIMS: ARCAimsWriter,
    ARCSectionName.SIGNIFICANCE: ARCSignificanceWriter,
    ARCSectionName.INNOVATION: ARCInnovationWriter,
    ARCSectionName.APPROACH: ARCApproachWriter,
    ARCSectionName.BENEFIT: ARCNationalBenefitWriter,
}

_SECTION_QUERIES: dict[ARCSectionName, str] = {
    ARCSectionName.OPENING: "summary aim contribution discovery",
    ARCSectionName.AIMS: "aim hypothesis objective research question",
    ARCSectionName.SIGNIFICANCE: "significance theory framework limitation gap",
    ARCSectionName.INNOVATION: "novel method technique framework approach",
    ARCSectionName.APPROACH: "methodology design protocol sample analysis",
    ARCSectionName.BENEFIT: "impact industry partner sector adoption benefit",
}

_SECTION_HEADINGS: dict[ARCSectionName, str] = {
    ARCSectionName.OPENING: "Project Description",
    ARCSectionName.AIMS: "Aims",
    ARCSectionName.SIGNIFICANCE: "Significance",
    ARCSectionName.INNOVATION: "Innovation",
    ARCSectionName.APPROACH: "Approach and Methodology",
    ARCSectionName.BENEFIT: "National Benefit",
}

_TOP_K_PER_SECTION = 6

_log = get_logger(__name__)
_result_cache: LRUCache[ARCResult] = LRUCache(get_settings().result_cache_size)


async def run_arc(
    request: ARCRequest,
    *,
    store: ReferenceStore | None = None,
    user_id: str | None = None,
) -> AsyncIterator[ARCEvent]:
    """Drive the full ARC pipeline, yielding one event per step."""
    store = store or get_reference_store()

    yield ARCEvent(
        "started",
        {"topic": request.topic, "scheme": request.scheme.value},
    )

    cache_key = hash_payload(
        {
            "kind": "arc",
            "request": request.model_dump(mode="json"),
            "user_id": user_id,
        }
    )
    cached = _result_cache.get(cache_key)
    if cached is not None:
        _log.info("arc_cache_hit", topic=request.topic, scheme=request.scheme.value)
        yield ARCEvent("completed", cached.model_dump())
        return

    settings = get_settings()
    try:
        with usage_scope(settings.max_tokens_per_request) as scope:
            async for event in _run_arc_inner(
                request, store=store, user_id=user_id
            ):
                if event.kind == "completed":
                    _result_cache.put(
                        cache_key, ARCResult.model_validate(event.payload)
                    )
                    yield ARCEvent("usage", scope.summary())
                yield event
            _log.info(
                "arc_completed",
                topic=request.topic,
                scheme=request.scheme.value,
                input_tokens=scope.input_tokens,
                output_tokens=scope.output_tokens,
                cache_read=scope.cache_read_tokens,
                requests=scope.requests,
                estimated_cost_usd=scope.estimated_cost_usd(),
            )
    except SpendCapExceeded as exc:
        yield ARCEvent("error", {"message": str(exc), "type": "SpendCapExceeded"})


async def _run_arc_inner(
    request: ARCRequest,
    *,
    store: ReferenceStore,
    user_id: str | None,
) -> AsyncIterator[ARCEvent]:
    meta = None
    index = None
    if request.set_id:
        meta = store.get_meta(request.set_id, user_id=user_id)
        index = store.get_index(request.set_id, user_id=user_id)
        if meta is None or index is None:
            yield ARCEvent("error", {"message": f"Unknown set_id: {request.set_id}"})
            return

    selected = set(request.sections)
    drafted: dict[ARCSectionName, str] = {}

    for section in CANONICAL_ARC_ORDER:
        if section not in selected:
            continue
        yield ARCEvent("section_started", {"section": section.value})

        chunks: list[Chunk] = []
        if index is not None:
            query = f"{request.topic} {_SECTION_QUERIES[section]}"
            chunks = [m.chunk for m in index.search(query, k=_TOP_K_PER_SECTION)]

        writer = _WRITERS[section]()
        draft = await writer.run(
            ARCWriterInput(
                topic=request.topic,
                scheme=request.scheme,
                innovation_type=request.innovation_type,
                section=section,
                discipline=request.discipline,
                notes=request.notes,
                chunks=chunks,
                other_sections={k.value: v for k, v in drafted.items()},
            )
        )
        drafted[section] = draft.content
        yield ARCEvent(
            "section_completed",
            {"section": section.value, "content": draft.content},
        )

    references: list[FormattedReference] = []
    if meta is not None and index is not None:
        sample_chunks = _sample_chunks_per_ref(meta, index)
        ref_output = await ReferenceFormatter().run(
            ReferenceFormatterInput(
                documents=meta.documents, sample_chunks_by_ref=sample_chunks
            )
        )
        references = ref_output.references
        yield ARCEvent("references_formatted", {"count": len(references)})

    grant = _assemble_grant(
        request=request, drafted=drafted, references=references
    )
    yield ARCEvent("grant_assembled", {"markdown": grant.markdown})

    yield ARCEvent("completed", ARCResult(grant=grant).model_dump())


def _sample_chunks_per_ref(meta, index) -> dict[str, list[str]]:
    out: dict[str, list[str]] = {}
    for doc in meta.documents:
        out[doc.ref_id] = [
            c.text[:300] for c in index.chunks if c.ref_id == doc.ref_id
        ][:2]
    return out


def _assemble_grant(
    *,
    request: ARCRequest,
    drafted: dict[ARCSectionName, str],
    references: list[FormattedReference],
) -> ARCGrantDraft:
    """Assemble final markdown — replace [ref=ID] markers with [N] citations."""
    ref_index: dict[str, int] = {r.ref_id: i + 1 for i, r in enumerate(references)}

    sections_out: dict[str, str] = {}
    parts: list[str] = [
        f"# ARC Grant Application — {request.topic}",
        "",
        f"**Scheme:** {request.scheme.value.replace('_', ' ').title()}    "
        f"**Innovation type:** {request.innovation_type.value.title()}",
        "",
    ]

    display_order = [
        ARCSectionName.OPENING,
        ARCSectionName.SIGNIFICANCE,
        ARCSectionName.INNOVATION,
        ARCSectionName.AIMS,
        ARCSectionName.APPROACH,
        ARCSectionName.BENEFIT,
    ]
    for section in display_order:
        if section not in drafted:
            continue
        body = _replace_refs(drafted[section], ref_index)
        sections_out[section.value] = body
        parts.append(f"## {_SECTION_HEADINGS[section]}")
        parts.append("")
        parts.append(body)
        parts.append("")

    if references:
        parts.append("## References")
        parts.append("")
        for i, ref in enumerate(references, start=1):
            parts.append(f"[{i}] {ref.citation}")
        parts.append("")

    return ARCGrantDraft(
        topic=request.topic,
        scheme=request.scheme,
        innovation_type=request.innovation_type,
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
