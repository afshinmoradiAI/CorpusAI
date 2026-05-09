"""Smoke tests for the section writers and reviewers.

The agents are structurally identical to Phase 2 — only the prompts differ —
so we test one writer end-to-end and one reviewer end-to-end. The workflow
test covers the rest.
"""

from __future__ import annotations

from dataclasses import dataclass

import pytest

from app.agents import BiologyReviewer, IntroductionWriter
from app.schemas.paper import (
    BiologyReview,
    ReviewerInput,
    SectionDraft,
    SectionName,
    WriterInput,
)
from app.schemas.papers import Chunk


@dataclass
class _FakeResponse:
    text: str


@pytest.mark.asyncio
async def test_introduction_writer_passes_chunks_through_renderer(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    agent = IntroductionWriter()

    captured = {}

    async def fake_run(message: str) -> _FakeResponse:
        captured["message"] = message
        return _FakeResponse(text='{"content":"draft introduction body."}')

    monkeypatch.setattr(agent._agent, "run", fake_run)

    chunks = [
        Chunk(chunk_id="c1", ref_id="r1", page=2, text="CRISPR background context"),
    ]
    result = await agent.run(
        WriterInput(
            topic="CRISPR off-target",
            section=SectionName.INTRODUCTION,
            chunks=chunks,
        )
    )

    assert isinstance(result, SectionDraft)
    assert "draft introduction" in result.content
    assert "ref=r1" in captured["message"]
    assert "p.2" in captured["message"]


@pytest.mark.asyncio
async def test_biology_reviewer_parses_structured_review(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    agent = BiologyReviewer()

    async def fake_run(_message: str) -> _FakeResponse:
        return _FakeResponse(
            text=(
                '{"summary":"OK","overall_score":3,'
                '"strengths":["clear aim"],'
                '"issues":[{"severity":"major","section":"methods","comment":"add controls"}]}'
            )
        )

    monkeypatch.setattr(agent._agent, "run", fake_run)
    review = await agent.run(ReviewerInput(topic="t", paper_markdown="# paper"))
    assert isinstance(review, BiologyReview)
    assert review.overall_score == 3
    assert review.issues[0].severity == "major"
