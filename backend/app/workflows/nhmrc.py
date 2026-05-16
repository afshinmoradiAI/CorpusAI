"""NHMRC grant workflow.

Generates the standard NHMRC grant sections in canonical order:
    Burden of Disease -> Aims & Hypotheses -> Methods ->
    Consumer & Community Involvement -> Significance & Impact ->
    Synopsis (written last)

If the user supplies a `set_id` (uploaded PDFs), each section is grounded
in BM25-retrieved excerpts from that reference set, and a reference list
is formatted at the end. If no PDFs are supplied, the workflow runs
without retrieval and emits no references.

The orchestrator yields typed `NHMRCEvent`s so the API can stream
progress over SSE.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from dataclasses import dataclass
from typing import Any, Literal

from app.agents import (
    BurdenOfDiseaseWriter,
    ConsumerInvolvementWriter,
    NHMRCAimsWriter,
    NHMRCImpactWriter,
    NHMRCMethodsWriter,
    NHMRCSynopsisWriter,
    ReferenceFormatter,
)
from app.agents.nhmrc_writers import _NHMRCWriter
from app.core.cache import LRUCache, hash_payload
from app.core.config import get_settings
from app.core.logging import get_logger
from app.core.usage import SpendCapExceeded, usage_scope
from app.schemas.nhmrc import (
    CANONICAL_NHMRC_ORDER,
    NHMRCGrantDraft,
    NHMRCRequest,
    NHMRCResult,
    NHMRCSectionName,
    NHMRCWriterInput,
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
class NHMRCEvent:
    kind: EventKind
    payload: dict[str, Any]


_WRITERS: dict[NHMRCSectionName, type[_NHMRCWriter]] = {
    NHMRCSectionName.SYNOPSIS: NHMRCSynopsisWriter,
    NHMRCSectionName.BURDEN: BurdenOfDiseaseWriter,
    NHMRCSectionName.AIMS: NHMRCAimsWriter,
    NHMRCSectionName.METHODS: NHMRCMethodsWriter,
    NHMRCSectionName.CONSUMER: ConsumerInvolvementWriter,
    NHMRCSectionName.IMPACT: NHMRCImpactWriter,
}

_SECTION_QUERIES: dict[NHMRCSectionName, str] = {
    NHMRCSectionName.SYNOPSIS: "summary background problem solution lay",
    NHMRCSectionName.BURDEN: "prevalence incidence mortality cost equity disparity",
    NHMRCSectionName.AIMS: "aim hypothesis primary outcome objective",
    NHMRCSectionName.METHODS: "methods design protocol randomisation sample size analysis",
    NHMRCSectionName.CONSUMER: "patient consumer community involvement co-design lived experience",
    NHMRCSectionName.IMPACT: "translation guideline policy implementation cost-effectiveness",
}

_SECTION_HEADINGS: dict[NHMRCSectionName, str] = {
    NHMRCSectionName.SYNOPSIS: "Synopsis (Plain Language Summary)",
    NHMRCSectionName.BURDEN: "Burden of Disease",
    NHMRCSectionName.AIMS: "Aims and Hypotheses",
    NHMRCSectionName.METHODS: "Research Plan / Methods",
    NHMRCSectionName.CONSUMER: "Consumer and Community Involvement",
    NHMRCSectionName.IMPACT: "Significance and Impact Pathway",
}

_TOP_K_PER_SECTION = 6

_log = get_logger(__name__)
_result_cache: LRUCache[NHMRCResult] = LRUCache(get_settings().result_cache_size)


async def run_nhmrc(
    request: NHMRCRequest,
    *,
    store: ReferenceStore | None = None,
    user_id: str | None = None,
) -> AsyncIterator[NHMRCEvent]:
    """Drive the full NHMRC pipeline, yielding one event per step."""
    store = store or get_reference_store()

    yield NHMRCEvent(
        "started",
        {"topic": request.topic, "scheme": request.scheme.value},
    )

    cache_key = hash_payload(
        {
            "kind": "nhmrc",
            "request": request.model_dump(mode="json"),
            "user_id": user_id,
        }
    )
    cached = _result_cache.get(cache_key)
    if cached is not None:
        _log.info("nhmrc_cache_hit", topic=request.topic, scheme=request.scheme.value)
        yield NHMRCEvent("completed", cached.model_dump())
        return

    settings = get_settings()
    try:
        with usage_scope(settings.max_tokens_per_request) as scope:
            async for event in _run_nhmrc_inner(
                request, store=store, user_id=user_id
            ):
                if event.kind == "completed":
                    _result_cache.put(
                        cache_key, NHMRCResult.model_validate(event.payload)
                    )
                    yield NHMRCEvent("usage", scope.summary())
                yield event
            _log.info(
                "nhmrc_completed",
                topic=request.topic,
                scheme=request.scheme.value,
                input_tokens=scope.input_tokens,
                output_tokens=scope.output_tokens,
                cache_read=scope.cache_read_tokens,
                requests=scope.requests,
                estimated_cost_usd=scope.estimated_cost_usd(),
            )
    except SpendCapExceeded as exc:
        yield NHMRCEvent("error", {"message": str(exc), "type": "SpendCapExceeded"})


async def _run_nhmrc_inner(
    request: NHMRCRequest,
    *,
    store: ReferenceStore,
    user_id: str | None,
) -> AsyncIterator[NHMRCEvent]:
    meta = None
    index = None
    if request.set_id:
        meta = store.get_meta(request.set_id, user_id=user_id)
        index = store.get_index(request.set_id, user_id=user_id)
        if meta is None or index is None:
            yield NHMRCEvent(
                "error", {"message": f"Unknown set_id: {request.set_id}"}
            )
            return

    selected = set(request.sections)
    drafted: dict[NHMRCSectionName, str] = {}

    for section in CANONICAL_NHMRC_ORDER:
        if section not in selected:
            continue
        yield NHMRCEvent("section_started", {"section": section.value})

        chunks: list[Chunk] = []
        if index is not None:
            query = f"{request.topic} {_SECTION_QUERIES[section]}"
            chunks = [m.chunk for m in index.search(query, k=_TOP_K_PER_SECTION)]

        writer = _WRITERS[section]()
        draft = await writer.run(
            NHMRCWriterInput(
                topic=request.topic,
                scheme=request.scheme,
                study_type=request.study_type,
                section=section,
                health_condition=request.health_condition,
                target_population=request.target_population,
                notes=request.notes,
                chunks=chunks,
                other_sections={k.value: v for k, v in drafted.items()},
            )
        )
        drafted[section] = draft.content
        yield NHMRCEvent(
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
        yield NHMRCEvent(
            "references_formatted", {"count": len(references)}
        )

    grant = _assemble_grant(
        request=request, drafted=drafted, references=references
    )
    yield NHMRCEvent("grant_assembled", {"markdown": grant.markdown})

    yield NHMRCEvent(
        "completed", NHMRCResult(grant=grant).model_dump()
    )


def _sample_chunks_per_ref(meta, index) -> dict[str, list[str]]:
    out: dict[str, list[str]] = {}
    for doc in meta.documents:
        out[doc.ref_id] = [
            c.text[:300] for c in index.chunks if c.ref_id == doc.ref_id
        ][:2]
    return out


def _assemble_grant(
    *,
    request: NHMRCRequest,
    drafted: dict[NHMRCSectionName, str],
    references: list[FormattedReference],
) -> NHMRCGrantDraft:
    """Assemble final markdown — replace [ref=ID] markers with [N] citations."""
    ref_index: dict[str, int] = {r.ref_id: i + 1 for i, r in enumerate(references)}

    sections_out: dict[str, str] = {}
    parts: list[str] = [
        f"# NHMRC Grant Application — {request.topic}",
        "",
        f"**Scheme:** {request.scheme.value.replace('_', ' ').title()}    "
        f"**Study type:** {request.study_type.value.replace('_', ' ').title()}",
        "",
    ]

    display_order = [
        NHMRCSectionName.SYNOPSIS,
        NHMRCSectionName.BURDEN,
        NHMRCSectionName.AIMS,
        NHMRCSectionName.METHODS,
        NHMRCSectionName.CONSUMER,
        NHMRCSectionName.IMPACT,
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

    return NHMRCGrantDraft(
        topic=request.topic,
        scheme=request.scheme,
        study_type=request.study_type,
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
