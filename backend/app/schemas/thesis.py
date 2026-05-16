"""Schemas for the Thesis pipeline."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field

from app.schemas.paper import FormattedReference
from app.schemas.papers import Chunk


class ThesisStructure(str, Enum):
    TRADITIONAL = "traditional"
    BY_PUBLICATION = "by_publication"
    HYBRID = "hybrid"
    MASTERS = "masters"
    CUSTOM = "custom"


class UploadedFigure(BaseModel):
    figure_id: str
    filename: str
    width_px: int | None = None
    height_px: int | None = None


class FigureRef(BaseModel):
    figure_id: str
    caption: str | None = None


class ChapterConfig(BaseModel):
    title: str | None = Field(default=None, max_length=200)
    notes: str | None = Field(default=None, max_length=4_000)
    set_id: str | None = None  # optional per-chapter PDFs
    figures: list[FigureRef] = Field(default_factory=list)


class ThesisRequest(BaseModel):
    title: str = Field(min_length=3, max_length=300)
    discipline: str | None = Field(default=None, max_length=200)
    structure: ThesisStructure = ThesisStructure.TRADITIONAL
    structure_notes: str | None = Field(default=None, max_length=2_000)
    chapters: list[ChapterConfig] = Field(min_length=1, max_length=15)


class ThesisChapterDraft(BaseModel):
    content: str


class ThesisChapterInput(BaseModel):
    thesis_title: str
    discipline: str | None = None
    structure: ThesisStructure
    structure_notes: str | None = None
    chapter_index: int  # 1-based
    chapter_count: int
    chapter_title: str
    chapter_notes: str | None = None
    figures: list[FigureRef] = Field(default_factory=list)
    chunks: list[Chunk] = Field(default_factory=list)
    other_chapters: dict[str, str] = Field(default_factory=dict)


class ThesisAbstractInput(BaseModel):
    thesis_title: str
    discipline: str | None = None
    chapter_summaries: dict[str, str]  # title -> chapter body


class ThesisDraft(BaseModel):
    title: str
    discipline: str | None
    structure: ThesisStructure
    abstract: str
    chapters: list[dict[str, str]]  # [{"title": ..., "content": ...}]
    references: list[FormattedReference] = Field(default_factory=list)
    figures: dict[str, UploadedFigure] = Field(default_factory=dict)
    markdown: str


class ThesisResult(BaseModel):
    thesis: ThesisDraft


# ---------- auto chapter titles ----------

_DEFAULT_MIDDLE: tuple[str, ...] = (
    "Literature Review",
    "Methodology",
    "Results",
    "Discussion",
)


def auto_chapter_title(index_1based: int, total: int) -> str:
    """Return a sensible default chapter title for a thesis of length `total`.

    Position 1 is always "Introduction"; position N is always "Conclusion".
    Middle positions cycle through Literature Review / Methodology /
    Results / Discussion.
    """
    if total == 1:
        return "Chapter 1: Introduction"
    if index_1based == 1:
        return "Chapter 1: Introduction"
    if index_1based == total:
        return f"Chapter {total}: Conclusion"
    middle_index = (index_1based - 2) % len(_DEFAULT_MIDDLE)
    return f"Chapter {index_1based}: {_DEFAULT_MIDDLE[middle_index]}"
