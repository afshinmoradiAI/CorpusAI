"""Pydantic models for the paper-writing pipeline (PDF ingestion + retrieval)."""

from __future__ import annotations

from pydantic import BaseModel, Field


class UploadedRef(BaseModel):
    """Metadata for one PDF the user has uploaded as a reference."""

    ref_id: str
    filename: str
    page_count: int
    char_count: int


class Chunk(BaseModel):
    """A retrievable text fragment from a reference paper."""

    chunk_id: str
    ref_id: str
    text: str
    page: int


class ChunkMatch(BaseModel):
    chunk: Chunk
    score: float


class RefSet(BaseModel):
    """A bundle of reference PDFs the user uploaded together."""

    set_id: str
    documents: list[UploadedRef] = Field(default_factory=list)


class SearchRequest(BaseModel):
    query: str = Field(min_length=1, max_length=500)
    k: int = Field(default=5, ge=1, le=30)
