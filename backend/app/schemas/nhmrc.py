"""Schemas for the NHMRC grant pipeline."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field

from app.schemas.papers import Chunk
from app.schemas.paper import FormattedReference


class NHMRCScheme(str, Enum):
    IDEAS = "ideas"
    INVESTIGATOR = "investigator"
    SYNERGY = "synergy"
    PARTNERSHIP = "partnership"
    CLINICAL_TRIAL = "clinical_trial"
    POSTGRADUATE = "postgraduate"


class StudyType(str, Enum):
    CLINICAL_TRIAL = "clinical_trial"
    OBSERVATIONAL = "observational"
    LABORATORY = "laboratory"
    HEALTH_SERVICES = "health_services"
    MIXED = "mixed"


class NHMRCSectionName(str, Enum):
    SYNOPSIS = "synopsis"
    BURDEN = "burden_of_disease"
    AIMS = "aims_hypotheses"
    METHODS = "methods"
    CONSUMER = "consumer_involvement"
    IMPACT = "significance_impact"


CANONICAL_NHMRC_ORDER: tuple[NHMRCSectionName, ...] = (
    NHMRCSectionName.BURDEN,
    NHMRCSectionName.AIMS,
    NHMRCSectionName.METHODS,
    NHMRCSectionName.CONSUMER,
    NHMRCSectionName.IMPACT,
    NHMRCSectionName.SYNOPSIS,  # plain-language summary written last
)


class NHMRCRequest(BaseModel):
    topic: str = Field(min_length=3, max_length=300)
    scheme: NHMRCScheme = NHMRCScheme.IDEAS
    study_type: StudyType = StudyType.LABORATORY
    health_condition: str | None = Field(default=None, max_length=200)
    target_population: str | None = Field(default=None, max_length=200)
    set_id: str | None = None  # optional uploaded-PDF reference set
    notes: str | None = Field(default=None, max_length=4_000)
    sections: list[NHMRCSectionName] = Field(
        default_factory=lambda: list(CANONICAL_NHMRC_ORDER)
    )


class NHMRCSectionDraft(BaseModel):
    content: str


class NHMRCWriterInput(BaseModel):
    topic: str
    scheme: NHMRCScheme
    study_type: StudyType
    section: NHMRCSectionName
    health_condition: str | None = None
    target_population: str | None = None
    notes: str | None = None
    chunks: list[Chunk] = Field(default_factory=list)
    other_sections: dict[str, str] = Field(default_factory=dict)


class NHMRCGrantDraft(BaseModel):
    topic: str
    scheme: NHMRCScheme
    study_type: StudyType
    sections: dict[str, str]
    references: list[FormattedReference] = Field(default_factory=list)
    markdown: str


class NHMRCResult(BaseModel):
    grant: NHMRCGrantDraft
