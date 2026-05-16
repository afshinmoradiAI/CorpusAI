"""Thesis chapter and abstract writers."""

from __future__ import annotations

from app.agents.base import BaseAgent
from app.schemas.thesis import (
    ThesisAbstractInput,
    ThesisChapterDraft,
    ThesisChapterInput,
)


class ThesisChapterWriter(BaseAgent[ThesisChapterInput, ThesisChapterDraft]):
    """One agent, invoked once per chapter."""

    prompt_name = "thesis_chapter_writer"
    output_model = ThesisChapterDraft

    def render_input(self, payload: ThesisChapterInput) -> str:
        parts: list[str] = [
            f"Thesis title: {payload.thesis_title}",
            f"Chapter {payload.chapter_index} of {payload.chapter_count}: "
            f"{payload.chapter_title}",
            f"Thesis structure: {payload.structure.value}",
        ]
        if payload.discipline:
            parts.append(f"Discipline: {payload.discipline}")
        if payload.structure_notes:
            parts.append(f"University structure notes:\n{payload.structure_notes}")
        if payload.chapter_notes:
            parts.append(f"\nWhat this chapter must cover:\n{payload.chapter_notes}")

        if payload.figures:
            lines = ["\nFigures available for this chapter (reference them inline):"]
            for f in payload.figures:
                caption = f.caption or "(no caption supplied)"
                lines.append(f"- figure_id={f.figure_id} — caption: {caption}")
            lines.append(
                "Reference figures inline as `[fig=ID]` (renders as 'Figure N'). "
                "Insert each figure where it should appear in the prose by placing "
                "`<<FIG=ID>>` on its own line."
            )
            parts.append("\n".join(lines))

        if payload.other_chapters:
            parts.append("\nAlready-drafted chapters (for context only):")
            for name, body in payload.other_chapters.items():
                parts.append(f"### {name}\n{body[:1500]}")

        if payload.chunks:
            parts.append("\nRelevant excerpts from this chapter's reference PDFs:")
            for i, c in enumerate(payload.chunks, start=1):
                parts.append(f"[{i}] (ref={c.ref_id}, p.{c.page})\n{c.text}")

        return "\n\n".join(parts)


class ThesisAbstractWriter(BaseAgent[ThesisAbstractInput, ThesisChapterDraft]):
    """Writes the thesis abstract from already-drafted chapters."""

    prompt_name = "thesis_abstract_writer"
    output_model = ThesisChapterDraft

    def render_input(self, payload: ThesisAbstractInput) -> str:
        parts: list[str] = [f"Thesis title: {payload.thesis_title}"]
        if payload.discipline:
            parts.append(f"Discipline: {payload.discipline}")
        parts.append("\nDrafted chapters (summarise each in the abstract):")
        for title, body in payload.chapter_summaries.items():
            parts.append(f"### {title}\n{body[:1500]}")
        return "\n\n".join(parts)
