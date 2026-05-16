"""Thesis workflow.

Drives chapter-by-chapter generation, then a single abstract pass,
then reference formatting (deduplicated across chapter PDFs), then
final assembly.

User inputs (`ThesisRequest`):
- Thesis title (required) + discipline (optional) + structure (preset).
- 1–15 chapters, each with optional title / notes / set_id / figures.

For each chapter:
1. Resolve title (auto-generate if blank).
2. If set_id present, BM25-retrieve top chunks for that chapter.
3. Run `ThesisChapterWriter` with chapter notes + figures + chunks.
4. Emit `chapter_completed` event.

After all chapters:
5. Run `ThesisAbstractWriter` over the drafted chapters.
6. Format references (union across all chapters' set_ids).
7. Assemble final markdown with global figure renumbering.
"""

from __future__ import annotations

import re
from collections.abc import AsyncIterator
from dataclasses import dataclass
from typing import Any, Literal

from app.agents import ReferenceFormatter, ThesisAbstractWriter, ThesisChapterWriter
from app.core.cache import LRUCache, hash_payload
from app.core.config import get_settings
from app.core.logging import get_logger
from app.core.usage import SpendCapExceeded, usage_scope
from app.schemas.paper import FormattedReference, ReferenceFormatterInput
from app.schemas.papers import Chunk, UploadedRef
from app.schemas.thesis import (
    ChapterConfig,
    FigureRef,
    ThesisAbstractInput,
    ThesisChapterInput,
    ThesisDraft,
    ThesisRequest,
    ThesisResult,
    UploadedFigure,
    auto_chapter_title,
)
from app.services import ReferenceStore, get_reference_store

EventKind = Literal[
    "started",
    "chapter_started",
    "chapter_completed",
    "abstract_started",
    "abstract_completed",
    "references_formatted",
    "thesis_assembled",
    "usage",
    "completed",
    "error",
]


@dataclass
class ThesisEvent:
    kind: EventKind
    payload: dict[str, Any]


_TOP_K_PER_CHAPTER = 8

_log = get_logger(__name__)
_result_cache: LRUCache[ThesisResult] = LRUCache(get_settings().result_cache_size)


async def run_thesis(
    request: ThesisRequest,
    *,
    store: ReferenceStore | None = None,
    user_id: str | None = None,
) -> AsyncIterator[ThesisEvent]:
    store = store or get_reference_store()
    yield ThesisEvent(
        "started",
        {"title": request.title, "chapter_count": len(request.chapters)},
    )

    cache_key = hash_payload(
        {
            "kind": "thesis",
            "request": request.model_dump(mode="json"),
            "user_id": user_id,
        }
    )
    cached = _result_cache.get(cache_key)
    if cached is not None:
        _log.info("thesis_cache_hit", title=request.title)
        yield ThesisEvent("completed", cached.model_dump())
        return

    settings = get_settings()
    try:
        with usage_scope(settings.max_tokens_per_request) as scope:
            async for event in _run_thesis_inner(
                request, store=store, user_id=user_id
            ):
                if event.kind == "completed":
                    _result_cache.put(
                        cache_key, ThesisResult.model_validate(event.payload)
                    )
                    yield ThesisEvent("usage", scope.summary())
                yield event
            _log.info(
                "thesis_completed",
                title=request.title,
                chapters=len(request.chapters),
                input_tokens=scope.input_tokens,
                output_tokens=scope.output_tokens,
                cache_read=scope.cache_read_tokens,
                requests=scope.requests,
                estimated_cost_usd=scope.estimated_cost_usd(),
            )
    except SpendCapExceeded as exc:
        yield ThesisEvent("error", {"message": str(exc), "type": "SpendCapExceeded"})


async def _run_thesis_inner(
    request: ThesisRequest,
    *,
    store: ReferenceStore,
    user_id: str | None,
) -> AsyncIterator[ThesisEvent]:
    chapter_count = len(request.chapters)
    resolved_titles: list[str] = []
    drafted: list[dict[str, str]] = []  # [{"title": ..., "content": ...}]

    for idx, chapter in enumerate(request.chapters, start=1):
        title = chapter.title or auto_chapter_title(idx, chapter_count)
        resolved_titles.append(title)
        yield ThesisEvent(
            "chapter_started", {"index": idx, "title": title}
        )

        chunks: list[Chunk] = []
        if chapter.set_id:
            meta = store.get_meta(chapter.set_id, user_id=user_id)
            index = store.get_index(chapter.set_id, user_id=user_id)
            if meta is None or index is None:
                yield ThesisEvent(
                    "error",
                    {"message": f"Unknown set_id for chapter {idx}: {chapter.set_id}"},
                )
                return
            query = f"{request.title} {title} {chapter.notes or ''}".strip()
            chunks = [m.chunk for m in index.search(query, k=_TOP_K_PER_CHAPTER)]

        writer = ThesisChapterWriter()
        draft = await writer.run(
            ThesisChapterInput(
                thesis_title=request.title,
                discipline=request.discipline,
                structure=request.structure,
                structure_notes=request.structure_notes,
                chapter_index=idx,
                chapter_count=chapter_count,
                chapter_title=title,
                chapter_notes=chapter.notes,
                figures=chapter.figures,
                chunks=chunks,
                other_chapters={c["title"]: c["content"] for c in drafted},
            )
        )
        drafted.append({"title": title, "content": draft.content})
        yield ThesisEvent(
            "chapter_completed",
            {"index": idx, "title": title, "content": draft.content},
        )

    yield ThesisEvent("abstract_started", {})
    abstract_draft = await ThesisAbstractWriter().run(
        ThesisAbstractInput(
            thesis_title=request.title,
            discipline=request.discipline,
            chapter_summaries={c["title"]: c["content"] for c in drafted},
        )
    )
    abstract_text = abstract_draft.content
    yield ThesisEvent("abstract_completed", {"content": abstract_text})

    documents: list[UploadedRef] = []
    sample_chunks: dict[str, list[str]] = {}
    seen_set_ids: set[str] = set()
    for chapter in request.chapters:
        sid = chapter.set_id
        if not sid or sid in seen_set_ids:
            continue
        seen_set_ids.add(sid)
        meta = store.get_meta(sid, user_id=user_id)
        index = store.get_index(sid, user_id=user_id)
        if meta is None or index is None:
            continue
        documents.extend(meta.documents)
        for doc in meta.documents:
            sample_chunks[doc.ref_id] = [
                c.text[:300] for c in index.chunks if c.ref_id == doc.ref_id
            ][:2]

    references: list[FormattedReference] = []
    if documents:
        ref_output = await ReferenceFormatter().run(
            ReferenceFormatterInput(
                documents=documents, sample_chunks_by_ref=sample_chunks
            )
        )
        references = ref_output.references
        yield ThesisEvent("references_formatted", {"count": len(references)})

    figure_lookup = _collect_figure_lookup(request.chapters)
    thesis = _assemble_thesis(
        request=request,
        chapters=drafted,
        abstract_text=abstract_text,
        references=references,
        figure_lookup=figure_lookup,
    )
    yield ThesisEvent("thesis_assembled", {"markdown": thesis.markdown})
    yield ThesisEvent("completed", ThesisResult(thesis=thesis).model_dump())


def _collect_figure_lookup(
    chapters: list[ChapterConfig],
) -> dict[str, FigureRef]:
    out: dict[str, FigureRef] = {}
    for ch in chapters:
        for f in ch.figures:
            out.setdefault(f.figure_id, f)
    return out


_FIG_INLINE_RE = re.compile(r"\[fig=([a-zA-Z0-9_\-]+)\]")
_FIG_BLOCK_RE = re.compile(r"^<<FIG=([a-zA-Z0-9_\-]+)>>$", re.MULTILINE)
_REF_INLINE_RE = re.compile(r"\[ref=([a-zA-Z0-9_\-]+)\]")


def _assemble_thesis(
    *,
    request: ThesisRequest,
    chapters: list[dict[str, str]],
    abstract_text: str,
    references: list[FormattedReference],
    figure_lookup: dict[str, FigureRef],
) -> ThesisDraft:
    """Assemble final thesis markdown.

    - Renumber `[fig=ID]` and `<<FIG=ID>>` markers globally (Figure 1, 2, ...)
      using order of first inline reference across chapters.
    - Replace inline `[fig=ID]` with "Figure N".
    - Replace block `<<FIG=ID>>` with a markdown image embed plus caption.
    - Renumber `[ref=ID]` markers using the reference index.
    """
    ref_index: dict[str, int] = {r.ref_id: i + 1 for i, r in enumerate(references)}

    figure_order: dict[str, int] = {}

    def next_figure_number(fid: str) -> int:
        if fid not in figure_order:
            figure_order[fid] = len(figure_order) + 1
        return figure_order[fid]

    parts: list[str] = [
        f"# {request.title}",
        "",
    ]
    if request.discipline:
        parts.append(f"*{request.discipline}*")
        parts.append("")

    parts.append("## Abstract")
    parts.append("")
    parts.append(_rewrite_refs(abstract_text, ref_index))
    parts.append("")

    parts.append("## Table of Contents")
    parts.append("")
    parts.append("- Abstract")
    for ch in chapters:
        parts.append(f"- {ch['title']}")
    if references:
        parts.append("- References")
    parts.append("")

    for ch in chapters:
        body = ch["content"]
        body = _rewrite_inline_figs(body, next_figure_number)
        body = _rewrite_block_figs(body, figure_lookup, next_figure_number)
        body = _rewrite_refs(body, ref_index)
        parts.append(f"## {ch['title']}")
        parts.append("")
        parts.append(body)
        parts.append("")

    if references:
        parts.append("## References")
        parts.append("")
        for i, ref in enumerate(references, start=1):
            parts.append(f"[{i}] {ref.citation}")
        parts.append("")

    return ThesisDraft(
        title=request.title,
        discipline=request.discipline,
        structure=request.structure,
        abstract=abstract_text,
        chapters=chapters,
        references=references,
        figures={},  # API populates this layer if needed
        markdown="\n".join(parts).strip() + "\n",
    )


def _rewrite_inline_figs(text: str, assign: Any) -> str:
    def sub(m: re.Match[str]) -> str:
        fid = m.group(1)
        n = assign(fid)
        return f"Figure {n}"

    return _FIG_INLINE_RE.sub(sub, text)


def _rewrite_block_figs(
    text: str,
    figures: dict[str, FigureRef],
    assign: Any,
) -> str:
    """Replace `<<FIG=ID>>` lines with a markdown image + caption block."""

    def sub(m: re.Match[str]) -> str:
        fid = m.group(1)
        n = assign(fid)
        ref = figures.get(fid)
        caption = (ref.caption if ref else None) or ""
        url = f"/api/thesis/figure/{fid}"
        alt = f"Figure {n}"
        caption_line = f"**Figure {n}.** {caption}".rstrip()
        # Blank line above and below the embed for clean markdown rendering.
        return f"\n![{alt}]({url})\n\n{caption_line}\n"

    return _FIG_BLOCK_RE.sub(sub, text)


def _rewrite_refs(text: str, ref_index: dict[str, int]) -> str:
    def sub(m: re.Match[str]) -> str:
        rid = m.group(1)
        n = ref_index.get(rid)
        return f"[{n}]" if n else "[?]"

    return _REF_INLINE_RE.sub(sub, text)
