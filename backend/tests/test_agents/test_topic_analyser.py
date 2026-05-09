"""Unit tests for TopicAnalyser.

These tests exercise the BaseAgent JSON parser and input renderer without
hitting the live Anthropic API — the agent's `_agent.run` is monkey-patched.
"""

from __future__ import annotations

from dataclasses import dataclass

import pytest

from app.agents.topic_analyser import TopicAnalyser
from app.schemas.research import TopicAnalysis, TopicRequest


@dataclass
class _FakeResponse:
    text: str


@pytest.mark.asyncio
async def test_topic_analyser_parses_fenced_json(monkeypatch: pytest.MonkeyPatch) -> None:
    agent = TopicAnalyser()

    async def fake_run(_message: str) -> _FakeResponse:
        return _FakeResponse(
            text=(
                "```json\n"
                '{"canonical_topic": "CRISPR-Cas9 off-target effects",\n'
                ' "keywords": ["crispr", "cas9", "off-target", "specificity"],\n'
                ' "sub_domains": ["primary T cells", "iPSC"]}\n'
                "```"
            )
        )

    monkeypatch.setattr(agent._agent, "run", fake_run)

    result = await agent.run(TopicRequest(topic="CRISPR off-target"))

    assert isinstance(result, TopicAnalysis)
    assert "crispr" in result.keywords
    assert len(result.sub_domains) == 2


def test_render_input_with_sub_field() -> None:
    agent = TopicAnalyser()
    rendered = agent.render_input(
        TopicRequest(topic="protein folding", sub_field="prion diseases")
    )
    assert "Topic: protein folding" in rendered
    assert "prion diseases" in rendered
