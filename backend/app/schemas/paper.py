"""Schemas for Write mode: section drafts, full paper, peer reviews."""

from __future__ import annotations

from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.papers import Chunk, UploadedRef


class SectionName(str, Enum):
    ABSTRACT = "abstract"
    INTRODUCTION = "introduction"
    METHODS = "methods"
    RESULTS = "results"
    DISCUSSION = "discussion"


CANONICAL_ORDER: tuple[SectionName, ...] = (
    SectionName.INTRODUCTION,
    SectionName.METHODS,
    SectionName.RESULTS,
    SectionName.DISCUSSION,
    SectionName.ABSTRACT,  # written last so it can reflect the rest
)


class WriteRequest(BaseModel):
    topic: str = Field(min_length=3, max_length=300)
    set_id: str
    sections: list[SectionName] = Field(min_length=1)
    user_results: str | None = Field(default=None, max_length=20_000)
    notes: str | None = Field(default=None, max_length=2_000)


class SectionDraft(BaseModel):
    content: str


class WriterInput(BaseModel):
    topic: str
    section: SectionName
    chunks: list[Chunk] = Field(default_factory=list)
    other_sections: dict[str, str] = Field(default_factory=dict)
    user_results: str | None = None
    notes: str | None = None


class FormattedReference(BaseModel):
    ref_id: str
    citation: str  # e.g. "Smith J. et al. (2023). Title. Journal."


class ReferenceFormatterInput(BaseModel):
    documents: list[UploadedRef]
    sample_chunks_by_ref: dict[str, list[str]] = Field(default_factory=dict)


class ReferenceFormatterOutput(BaseModel):
    references: list[FormattedReference]


class PaperDraft(BaseModel):
    topic: str
    sections: dict[str, str]  # SectionName.value -> content
    references: list[FormattedReference] = Field(default_factory=list)
    markdown: str


# ---------- Reviewer models ----------


Severity = Literal["critical", "major", "minor"]


class ReviewIssue(BaseModel):
    severity: Severity
    section: str
    comment: str


class BiologyReview(BaseModel):
    summary: str
    overall_score: int = Field(ge=1, le=5)
    strengths: list[str] = Field(default_factory=list)
    issues: list[ReviewIssue] = Field(default_factory=list)


class StatisticsReview(BaseModel):
    summary: str
    overall_score: int = Field(ge=1, le=5)
    strengths: list[str] = Field(default_factory=list)
    issues: list[ReviewIssue] = Field(default_factory=list)


class GapReview(BaseModel):
    summary: str
    unaddressed_gaps: list[str] = Field(default_factory=list)
    future_work: list[str] = Field(default_factory=list)


class ReviewerInput(BaseModel):
    topic: str
    paper_markdown: str


class ReviewSynthesis(BaseModel):
    executive_summary: str
    top_revisions: list[str] = Field(default_factory=list)


class ReviewSynthesisInput(BaseModel):
    topic: str
    biology: BiologyReview
    statistics: StatisticsReview
    gap: GapReview


class ReviewReport(BaseModel):
    biology: BiologyReview
    statistics: StatisticsReview
    gap: GapReview
    synthesis: ReviewSynthesis


class WriteResult(BaseModel):
    paper: PaperDraft
    review: ReviewReport | None = None
