"""NHMRC grant section writers.

All six writers share the same input/output shape; only their prompt file
differs. They consume the topic, scheme, study type, retrieved chunks
(optional), already-written sections, and free-form user notes.
"""

from __future__ import annotations

from app.agents.base import BaseAgent
from app.schemas.nhmrc import NHMRCSectionDraft, NHMRCWriterInput


class _NHMRCWriter(BaseAgent[NHMRCWriterInput, NHMRCSectionDraft]):
    """Common rendering logic shared by all NHMRC section writers."""

    output_model = NHMRCSectionDraft

    def render_input(self, payload: NHMRCWriterInput) -> str:
        parts: list[str] = [
            f"Topic: {payload.topic}",
            f"NHMRC scheme: {payload.scheme.value}",
            f"Study type: {payload.study_type.value}",
            f"Section: {payload.section.value}",
        ]

        if payload.health_condition:
            parts.append(f"Health condition: {payload.health_condition}")
        if payload.target_population:
            parts.append(f"Target population: {payload.target_population}")
        if payload.notes:
            parts.append(f"\nUser notes:\n{payload.notes}")

        if payload.other_sections:
            parts.append("\nAlready-drafted sections (for context):")
            for name, body in payload.other_sections.items():
                parts.append(f"### {name}\n{body}")

        if payload.chunks:
            parts.append("\nRelevant excerpts from reference papers:")
            for i, c in enumerate(payload.chunks, start=1):
                parts.append(f"[{i}] (ref={c.ref_id}, p.{c.page})\n{c.text}")

        return "\n\n".join(parts)


class NHMRCSynopsisWriter(_NHMRCWriter):
    prompt_name = "nhmrc_synopsis_writer"


class BurdenOfDiseaseWriter(_NHMRCWriter):
    prompt_name = "nhmrc_burden_writer"


class NHMRCAimsWriter(_NHMRCWriter):
    prompt_name = "nhmrc_aims_writer"


class NHMRCMethodsWriter(_NHMRCWriter):
    prompt_name = "nhmrc_methods_writer"


class ConsumerInvolvementWriter(_NHMRCWriter):
    prompt_name = "nhmrc_consumer_writer"


class NHMRCImpactWriter(_NHMRCWriter):
    prompt_name = "nhmrc_impact_writer"
