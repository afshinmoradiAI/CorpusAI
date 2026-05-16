"""ARC grant section writers.

All six writers share the same input/output shape; only their prompt file
differs.
"""

from __future__ import annotations

from app.agents.base import BaseAgent
from app.schemas.arc import ARCSectionDraft, ARCWriterInput


class _ARCWriter(BaseAgent[ARCWriterInput, ARCSectionDraft]):
    """Common rendering logic shared by all ARC section writers."""

    output_model = ARCSectionDraft

    def render_input(self, payload: ARCWriterInput) -> str:
        parts: list[str] = [
            f"Topic: {payload.topic}",
            f"ARC scheme: {payload.scheme.value}",
            f"Innovation type: {payload.innovation_type.value}",
            f"Section: {payload.section.value}",
        ]

        if payload.discipline:
            parts.append(f"Discipline: {payload.discipline}")
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


class ARCOpeningWriter(_ARCWriter):
    prompt_name = "arc_opening_writer"


class ARCAimsWriter(_ARCWriter):
    prompt_name = "arc_aims_writer"


class ARCSignificanceWriter(_ARCWriter):
    prompt_name = "arc_significance_writer"


class ARCInnovationWriter(_ARCWriter):
    prompt_name = "arc_innovation_writer"


class ARCApproachWriter(_ARCWriter):
    prompt_name = "arc_approach_writer"


class ARCNationalBenefitWriter(_ARCWriter):
    prompt_name = "arc_benefit_writer"
