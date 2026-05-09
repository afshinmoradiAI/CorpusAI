"""Section writers for Write mode.

All five writers share the same input/output shape; only their prompt
file differs. They each consume retrieved chunks, optionally already-written
sections, and any user-provided context (notes, raw results data).
"""

from __future__ import annotations

from app.agents.base import BaseAgent
from app.schemas.paper import SectionDraft, WriterInput


class _SectionWriter(BaseAgent[WriterInput, SectionDraft]):
    """Common rendering logic shared by all section writers."""

    output_model = SectionDraft

    def render_input(self, payload: WriterInput) -> str:
        parts: list[str] = [f"Topic: {payload.topic}", f"Section: {payload.section.value}"]

        if payload.notes:
            parts.append(f"\nUser notes:\n{payload.notes}")
        if payload.user_results:
            parts.append(f"\nUser-provided results / data:\n{payload.user_results}")

        if payload.other_sections:
            parts.append("\nAlready-drafted sections (for context):")
            for name, body in payload.other_sections.items():
                parts.append(f"### {name}\n{body}")

        if payload.chunks:
            parts.append("\nRelevant excerpts from reference papers:")
            for i, c in enumerate(payload.chunks, start=1):
                parts.append(f"[{i}] (ref={c.ref_id}, p.{c.page})\n{c.text}")
        else:
            parts.append("\n(No reference excerpts retrieved for this section.)")

        return "\n\n".join(parts)


class AbstractWriter(_SectionWriter):
    prompt_name = "abstract_writer"


class IntroductionWriter(_SectionWriter):
    prompt_name = "introduction_writer"


class MethodsWriter(_SectionWriter):
    prompt_name = "methods_writer"


class ResultsWriter(_SectionWriter):
    prompt_name = "results_writer"


class DiscussionWriter(_SectionWriter):
    prompt_name = "discussion_writer"
