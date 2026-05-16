"""Schemas for the ARC grant pipeline."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field

from app.schemas.paper import FormattedReference
from app.schemas.papers import Chunk


class ARCScheme(str, Enum):
    DISCOVERY = "discovery"
    LINKAGE = "linkage"
    LAUREATE = "laureate"
    DECRA = "decra"
    FUTURE = "future"
    CENTRE = "centre"


class InnovationType(str, Enum):
    CONCEPTUAL = "conceptual"
    METHODOLOGICAL = "methodological"
    EMPIRICAL = "empirical"
    INTEGRATIVE = "integrative"


class ARCSectionName(str, Enum):
    OPENING = "opening_statement"
    AIMS = "aims"
    SIGNIFICANCE = "significance"
    INNOVATION = "innovation"
    APPROACH = "approach_methodology"
    BENEFIT = "national_benefit"


CANONICAL_ARC_ORDER: tuple[ARCSectionName, ...] = (
    ARCSectionName.SIGNIFICANCE,
    ARCSectionName.INNOVATION,
    ARCSectionName.AIMS,
    ARCSectionName.APPROACH,
    ARCSectionName.BENEFIT,
    ARCSectionName.OPENING,  # written last, placed first
)


class ARCRequest(BaseModel):
    topic: str = Field(min_length=3, max_length=300)
    scheme: ARCScheme = ARCScheme.DISCOVERY
    innovation_type: InnovationType = InnovationType.METHODOLOGICAL
    discipline: str | None = Field(default=None, max_length=200)
    set_id: str | None = None
    notes: str | None = Field(default=None, max_length=4_000)
    sections: list[ARCSectionName] = Field(
        default_factory=lambda: list(CANONICAL_ARC_ORDER)
    )


class ARCSectionDraft(BaseModel):
    content: str


class ARCWriterInput(BaseModel):
    topic: str
    scheme: ARCScheme
    innovation_type: InnovationType
    section: ARCSectionName
    discipline: str | None = None
    notes: str | None = None
    chunks: list[Chunk] = Field(default_factory=list)
    other_sections: dict[str, str] = Field(default_factory=dict)


class ARCGrantDraft(BaseModel):
    topic: str
    scheme: ARCScheme
    innovation_type: InnovationType
    sections: dict[str, str]
    references: list[FormattedReference] = Field(default_factory=list)
    markdown: str


class ARCResult(BaseModel):
    grant: ARCGrantDraft
