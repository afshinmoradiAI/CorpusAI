"""Pydantic models for the Explore (idea-generation) pipeline."""

from __future__ import annotations

from pydantic import BaseModel, Field


class TopicRequest(BaseModel):
    topic: str = Field(min_length=3, max_length=300)
    sub_field: str | None = Field(default=None, max_length=120)


class TopicAnalysis(BaseModel):
    canonical_topic: str
    keywords: list[str] = Field(min_length=3, max_length=12)
    sub_domains: list[str] = Field(min_length=1, max_length=6)


class RawPaper(BaseModel):
    """Unprocessed result returned by the Semantic Scholar service."""

    source_id: str
    title: str
    abstract: str | None = None
    year: int | None = None
    authors: list[str] = Field(default_factory=list)
    venue: str | None = None
    citation_count: int | None = None
    url: str | None = None


class PaperSummary(BaseModel):
    title: str
    year: int | None = None
    authors: list[str] = Field(default_factory=list)
    findings: list[str] = Field(default_factory=list)
    methods: list[str] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)
    source_id: str | None = None


class PaperSummariserInput(BaseModel):
    paper: RawPaper


class ResearchGap(BaseModel):
    description: str
    evidence: list[str] = Field(default_factory=list)


class GapFinderInput(BaseModel):
    topic: str
    summaries: list[PaperSummary]


class ResearchIdea(BaseModel):
    idea: str


class IdeaGeneratorInput(BaseModel):
    topic: str
    gap: ResearchGap
    summaries: list[PaperSummary]


class HypotheticalMethod(BaseModel):
    method: str


class MethodDesignerInput(BaseModel):
    topic: str
    gap: ResearchGap
    idea: str


class DiscussionParagraph(BaseModel):
    discussion: str


class DiscussionWriterInput(BaseModel):
    topic: str
    gap: ResearchGap
    idea: str
    method: str


class ResearchOutput(BaseModel):
    topic: str
    gap: ResearchGap
    idea: str
    method: str
    discussion: str
    references: list[PaperSummary] = Field(default_factory=list)
