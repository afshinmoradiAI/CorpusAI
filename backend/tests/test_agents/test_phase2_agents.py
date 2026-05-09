"""Smoke tests for the five Phase-2 agents.

Each test monkey-patches `agent._agent.run` to skip the live LLM call,
then verifies the input renderer and JSON parser cooperate.
"""

from __future__ import annotations

from dataclasses import dataclass

import pytest

from app.agents import (
    ExploreDiscussionWriter,
    GapFinder,
    IdeaGenerator,
    MethodDesigner,
    PaperSummariser,
)
from app.schemas.research import (
    DiscussionWriterInput,
    GapFinderInput,
    IdeaGeneratorInput,
    MethodDesignerInput,
    PaperSummariserInput,
    PaperSummary,
    RawPaper,
    ResearchGap,
)


@dataclass
class _FakeResponse:
    text: str


def _patch(agent_obj, json_payload: str, monkeypatch: pytest.MonkeyPatch) -> None:
    async def fake_run(_message: str) -> _FakeResponse:
        return _FakeResponse(text=json_payload)

    monkeypatch.setattr(agent_obj._agent, "run", fake_run)


@pytest.mark.asyncio
async def test_paper_summariser(monkeypatch: pytest.MonkeyPatch) -> None:
    agent = PaperSummariser()
    _patch(
        agent,
        """{"title":"X","year":2024,"authors":["A"],
            "findings":["f1"],"methods":["m1"],"limitations":["l1"],
            "source_id":"s1"}""",
        monkeypatch,
    )
    result = await agent.run(
        PaperSummariserInput(
            paper=RawPaper(source_id="s1", title="X", abstract="abc", year=2024)
        )
    )
    assert isinstance(result, PaperSummary)
    assert result.findings == ["f1"]


@pytest.mark.asyncio
async def test_gap_finder(monkeypatch: pytest.MonkeyPatch) -> None:
    agent = GapFinder()
    _patch(
        agent,
        '{"description":"no longitudinal data","evidence":["paper X is cross-sectional"]}',
        monkeypatch,
    )
    result = await agent.run(
        GapFinderInput(
            topic="t",
            summaries=[PaperSummary(title="X", findings=["f"])],
        )
    )
    assert "longitudinal" in result.description


@pytest.mark.asyncio
async def test_idea_generator(monkeypatch: pytest.MonkeyPatch) -> None:
    agent = IdeaGenerator()
    _patch(agent, '{"idea":"do a longitudinal cohort..."}', monkeypatch)
    result = await agent.run(
        IdeaGeneratorInput(
            topic="t",
            gap=ResearchGap(description="d"),
            summaries=[],
        )
    )
    assert "longitudinal" in result.idea


@pytest.mark.asyncio
async def test_method_designer(monkeypatch: pytest.MonkeyPatch) -> None:
    agent = MethodDesigner()
    _patch(agent, '{"method":"recruit n=50 participants..."}', monkeypatch)
    result = await agent.run(
        MethodDesignerInput(
            topic="t", gap=ResearchGap(description="d"), idea="i"
        )
    )
    assert "n=50" in result.method


@pytest.mark.asyncio
async def test_discussion_writer(monkeypatch: pytest.MonkeyPatch) -> None:
    agent = ExploreDiscussionWriter()
    _patch(agent, '{"discussion":"This work aims to..."}', monkeypatch)
    result = await agent.run(
        DiscussionWriterInput(
            topic="t", gap=ResearchGap(description="d"), idea="i", method="m"
        )
    )
    assert result.discussion.startswith("This work")
