"""Smoke tests for the five Phase-2 agents.

Each test monkey-patches `BaseAgent.run` to skip the live LLM call, then
verifies the input renderer + output parser cooperate (via `_parse`).
"""

from __future__ import annotations

import pytest

from app.agents import (
    ExploreDiscussionWriter,
    GapFinder,
    IdeaGenerator,
    MethodDesigner,
    PaperSummariser,
)
from app.agents.base import BaseAgent
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


def _patch(
    json_payload: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    async def fake_run(self: BaseAgent, _payload):  # type: ignore[no-untyped-def]
        return self._parse(json_payload)

    monkeypatch.setattr(BaseAgent, "run", fake_run)


@pytest.mark.asyncio
async def test_paper_summariser(monkeypatch: pytest.MonkeyPatch) -> None:
    _patch(
        """{"title":"X","year":2024,"authors":["A"],
            "findings":["f1"],"methods":["m1"],"limitations":["l1"],
            "source_id":"s1"}""",
        monkeypatch,
    )
    agent = PaperSummariser()
    result = await agent.run(
        PaperSummariserInput(
            paper=RawPaper(source_id="s1", title="X", abstract="abc", year=2024)
        )
    )
    assert isinstance(result, PaperSummary)
    assert result.findings == ["f1"]


@pytest.mark.asyncio
async def test_gap_finder(monkeypatch: pytest.MonkeyPatch) -> None:
    _patch(
        '{"description":"no longitudinal data","evidence":["paper X is cross-sectional"]}',
        monkeypatch,
    )
    agent = GapFinder()
    result = await agent.run(
        GapFinderInput(
            topic="t",
            summaries=[PaperSummary(title="X", findings=["f"])],
        )
    )
    assert "longitudinal" in result.description


@pytest.mark.asyncio
async def test_idea_generator(monkeypatch: pytest.MonkeyPatch) -> None:
    _patch('{"idea":"do a longitudinal cohort..."}', monkeypatch)
    agent = IdeaGenerator()
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
    _patch('{"method":"recruit n=50 participants..."}', monkeypatch)
    agent = MethodDesigner()
    result = await agent.run(
        MethodDesignerInput(
            topic="t", gap=ResearchGap(description="d"), idea="i"
        )
    )
    assert "n=50" in result.method


@pytest.mark.asyncio
async def test_discussion_writer(monkeypatch: pytest.MonkeyPatch) -> None:
    _patch('{"discussion":"This work aims to..."}', monkeypatch)
    agent = ExploreDiscussionWriter()
    result = await agent.run(
        DiscussionWriterInput(
            topic="t", gap=ResearchGap(description="d"), idea="i", method="m"
        )
    )
    assert result.discussion.startswith("This work")
