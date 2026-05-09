"""ReferenceFormatter — turns uploaded ref metadata into a numbered list.

The reviewer/writer chain emits inline `[ref=<ref_id>]` markers; the assembler
replaces them with `[N]` while building the final markdown. This agent's job
is to produce the human-readable citation strings — APA-ish format, since we
do not have a structured CSL parser yet.
"""

from app.agents.base import BaseAgent
from app.schemas.paper import (
    ReferenceFormatterInput,
    ReferenceFormatterOutput,
)


class ReferenceFormatter(BaseAgent[ReferenceFormatterInput, ReferenceFormatterOutput]):
    prompt_name = "reference_formatter"
    output_model = ReferenceFormatterOutput

    def render_input(self, payload: ReferenceFormatterInput) -> str:
        lines = ["Reference papers (formatted from uploaded PDFs):"]
        for doc in payload.documents:
            samples = payload.sample_chunks_by_ref.get(doc.ref_id, [])
            sample_text = "\n".join(f"- {s[:280]}" for s in samples[:2]) or "(no excerpts)"
            lines.append(
                f"\nref_id: {doc.ref_id}\n"
                f"filename: {doc.filename}\n"
                f"pages: {doc.page_count}\n"
                f"first excerpts:\n{sample_text}"
            )
        return "\n".join(lines)
