"""PaperSummariser — converts a RawPaper (title + abstract) into a PaperSummary."""

from app.agents.base import BaseAgent
from app.core.config import get_settings
from app.schemas.research import PaperSummariserInput, PaperSummary


class PaperSummariser(BaseAgent[PaperSummariserInput, PaperSummary]):
    prompt_name = "paper_summariser"
    output_model = PaperSummary
    model = get_settings().anthropic_fast_model  # Haiku: structured extraction

    def render_input(self, payload: PaperSummariserInput) -> str:
        p = payload.paper
        authors = ", ".join(p.authors) if p.authors else "unknown"
        return (
            f"Title: {p.title}\n"
            f"Year: {p.year if p.year is not None else 'unknown'}\n"
            f"Authors: {authors}\n"
            f"Source ID: {p.source_id}\n"
            f"Abstract:\n{p.abstract or '(no abstract)'}\n"
        )
