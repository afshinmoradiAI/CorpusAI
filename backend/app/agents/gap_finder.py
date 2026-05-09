"""GapFinder — identifies one research gap from a list of paper summaries."""

from app.agents.base import BaseAgent
from app.schemas.research import GapFinderInput, ResearchGap


class GapFinder(BaseAgent[GapFinderInput, ResearchGap]):
    prompt_name = "gap_finder"
    output_model = ResearchGap

    def render_input(self, payload: GapFinderInput) -> str:
        lines = [f"Topic: {payload.topic}", "", "Paper summaries:"]
        for i, s in enumerate(payload.summaries, start=1):
            findings = "; ".join(s.findings) or "(none)"
            limitations = "; ".join(s.limitations) or "(none)"
            lines.append(
                f"{i}. {s.title} ({s.year or 'n.d.'})\n"
                f"   findings: {findings}\n"
                f"   limitations: {limitations}"
            )
        return "\n".join(lines)
