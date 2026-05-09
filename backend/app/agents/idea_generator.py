"""IdeaGenerator — proposes a novel research idea targeting the gap."""

from app.agents.base import BaseAgent
from app.schemas.research import IdeaGeneratorInput, ResearchIdea


class IdeaGenerator(BaseAgent[IdeaGeneratorInput, ResearchIdea]):
    prompt_name = "idea_generator"
    output_model = ResearchIdea

    def render_input(self, payload: IdeaGeneratorInput) -> str:
        evidence = "\n".join(f"- {e}" for e in payload.gap.evidence) or "- (none)"
        return (
            f"Topic: {payload.topic}\n\n"
            f"Identified gap:\n{payload.gap.description}\n\n"
            f"Evidence supporting the gap:\n{evidence}\n\n"
            f"Number of papers reviewed: {len(payload.summaries)}"
        )
