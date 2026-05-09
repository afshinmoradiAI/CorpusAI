"""ExploreDiscussionWriter — aim + importance paragraph for an idea proposal.

Distinct from the Write-mode DiscussionWriter, which writes the Discussion
*section* of an academic paper. This one closes the Explore pipeline.
"""

from app.agents.base import BaseAgent
from app.schemas.research import DiscussionParagraph, DiscussionWriterInput


class ExploreDiscussionWriter(BaseAgent[DiscussionWriterInput, DiscussionParagraph]):
    prompt_name = "explore_discussion_writer"
    output_model = DiscussionParagraph

    def render_input(self, payload: DiscussionWriterInput) -> str:
        return (
            f"Topic: {payload.topic}\n\n"
            f"Gap: {payload.gap.description}\n\n"
            f"Idea:\n{payload.idea}\n\n"
            f"Method:\n{payload.method}"
        )
