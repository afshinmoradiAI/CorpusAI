"""End-to-end test of the Explore workflow with all LLM calls and the
Semantic Scholar HTTP call mocked. Verifies the event stream order,
the typed payloads, and the final ResearchOutput.
"""

from __future__ import annotations

from dataclasses import dataclass

import pytest

from app.agents.base import BaseAgent
from app.schemas.research import RawPaper, TopicRequest
from app.workflows import explore as explore_module


@dataclass
class _FakeResponse:
    text: str


CANNED: dict[str, str] = {
    "topic_analyser": (
        '{"canonical_topic":"CRISPR off-target",'
        '"keywords":["crispr","cas9","off-target","specificity"],'
        '"sub_domains":["primary T cells"]}'
    ),
    "paper_summariser": (
        '{"title":"Paper","year":2024,"authors":["A"],'
        '"findings":["f"],"methods":["m"],"limitations":["l"],"source_id":"s"}'
    ),
    "gap_finder": (
        '{"description":"missing in vivo validation",'
        '"evidence":["all reviewed papers are in vitro"]}'
    ),
    "idea_generator": '{"idea":"perform an in vivo CRISPR off-target screen in mice..."}',
    "method_designer": (
        '{"method":"inject AAV-Cas9 into n=20 C57BL/6 mice per arm..."}'
    ),
    "explore_discussion_writer": (
        '{"discussion":"This work aims to close the in-vivo validation gap..."}'
    ),
}


@pytest.fixture(autouse=True)
def _patch_llm(monkeypatch: pytest.MonkeyPatch) -> None:
    """Replace BaseAgent.run with a router keyed on the prompt name."""

    async def fake_run(self: BaseAgent, payload):  # type: ignore[no-untyped-def]
        text = CANNED[self.prompt_name]
        return self._parse(text)

    monkeypatch.setattr(BaseAgent, "run", fake_run)


@pytest.fixture
def fake_search():
    async def _search(query: str, *, limit: int = 8):  # noqa: ARG001
        return [
            RawPaper(
                source_id=f"s{i}",
                title=f"Paper {i}",
                abstract="abstract text",
                year=2024,
            )
            for i in range(3)
        ]

    return _search


@pytest.mark.asyncio
async def test_run_explore_emits_full_event_sequence(fake_search) -> None:
    events = []
    async for ev in explore_module.run_explore(
        TopicRequest(topic="CRISPR off-target"),
        paper_limit=3,
        search_fn=fake_search,
    ):
        events.append(ev)

    kinds = [e.kind for e in events]
    assert kinds == [
        "started",
        "topic_analysed",
        "papers_found",
        "papers_summarised",
        "gap_found",
        "idea_generated",
        "method_designed",
        "discussion_written",
        "completed",
    ]

    final = events[-1].payload
    assert final["topic"] == "CRISPR off-target"
    assert "in vivo" in final["idea"]
    assert "n=20" in final["method"]
    assert len(final["references"]) == 3


@pytest.mark.asyncio
async def test_run_explore_aborts_on_no_papers() -> None:
    async def empty_search(query: str, *, limit: int = 8):  # noqa: ARG001
        return []

    events = []
    async for ev in explore_module.run_explore(
        TopicRequest(topic="empty topic"), paper_limit=3, search_fn=empty_search
    ):
        events.append(ev)

    assert events[-1].kind == "error"
