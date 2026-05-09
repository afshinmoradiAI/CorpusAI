"""MethodDesigner — drafts a hypothetical experimental method for the idea."""

from app.agents.base import BaseAgent
from app.schemas.research import HypotheticalMethod, MethodDesignerInput


class MethodDesigner(BaseAgent[MethodDesignerInput, HypotheticalMethod]):
    prompt_name = "method_designer"
    output_model = HypotheticalMethod

    def render_input(self, payload: MethodDesignerInput) -> str:
        return (
            f"Topic: {payload.topic}\n\n"
            f"Gap: {payload.gap.description}\n\n"
            f"Idea:\n{payload.idea}"
        )
