"""TopicAnalyser — first agent in the Explore pipeline.

Takes a free-form biology topic and produces a canonical phrasing,
search keywords, and narrower sub-domains for the LiteratureSearcher.
"""

from app.agents.base import BaseAgent
from app.core.config import get_settings
from app.schemas.research import TopicAnalysis, TopicRequest


class TopicAnalyser(BaseAgent[TopicRequest, TopicAnalysis]):
    prompt_name = "topic_analyser"
    output_model = TopicAnalysis
    model = get_settings().anthropic_fast_model  # Haiku: keyword expansion

    def render_input(self, payload: TopicRequest) -> str:
        if payload.sub_field:
            return f"Topic: {payload.topic}\nSub-field hint: {payload.sub_field}"
        return f"Topic: {payload.topic}"
