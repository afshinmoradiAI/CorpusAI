"""End-to-end test of the Write workflow with all LLM calls mocked.

A small in-memory ReferenceStore is populated with a synthesised PDF, then
`run_write` is exercised over a 3-section selection. We verify:
- the event sequence,
- each section produces a `section_completed` event,
- citation markers are rewritten from `[ref=...]` to numbered form,
- the review pipeline produces a synthesised report,
- the final WriteResult is well-formed.
"""

from __future__ import annotations

import io

import pytest
from reportlab.pdfgen import canvas  # type: ignore[import-untyped]

from app.agents.base import BaseAgent
from app.schemas.paper import SectionName, WriteRequest
from app.services.reference_store import ReferenceStore
from app.workflows import write as write_module


def _pdf(text: str) -> bytes:
    buf = io.BytesIO()
    c = canvas.Canvas(buf)
    c.drawString(72, 720, text)
    c.showPage()
    c.save()
    return buf.getvalue()


CANNED: dict[str, str] = {
    "introduction_writer": '{"content":"Intro body referencing [ref=__FIRST__]."}',
    "methods_writer": '{"content":"### Study design\\nWe describe methods [ref=__FIRST__]."}',
    "discussion_writer": '{"content":"We discuss findings."}',
    "abstract_writer": '{"content":"Abstract paragraph summarising."}',
    "results_writer": '{"content":"Results synthesised from refs."}',
    "reference_formatter": (
        '{"references":[{"ref_id":"__FIRST__","citation":"Doe J. (2024). Title. Journal."}]}'
    ),
    "biology_reviewer": (
        '{"summary":"ok","overall_score":3,"strengths":["s"],'
        '"issues":[{"severity":"minor","section":"methods","comment":"c"}]}'
    ),
    "statistics_reviewer": (
        '{"summary":"ok","overall_score":3,"strengths":["s"],'
        '"issues":[]}'
    ),
    "gap_reviewer": (
        '{"summary":"ok","unaddressed_gaps":["no in vivo data"],"future_work":["mouse model"]}'
    ),
    "review_synthesiser": (
        '{"executive_summary":"Generally sound draft.",'
        '"top_revisions":["Add controls.","Power analysis."]}'
    ),
}


@pytest.fixture
async def loaded_store() -> tuple[ReferenceStore, str, str]:
    store = ReferenceStore()
    pdf = _pdf("CRISPR off-target effects in human T cells. " * 50)
    meta = await store.create_set([("paper1.pdf", pdf)])
    ref_id = meta.documents[0].ref_id
    return store, meta.set_id, ref_id


@pytest.fixture(autouse=True)
async def _patch_llm(monkeypatch: pytest.MonkeyPatch, loaded_store) -> None:
    """Route every BaseAgent.run by prompt name to a canned reply.

    `__FIRST__` is substituted with the real ref_id so the assembler's
    citation rewriter has a key to match on.
    """
    _, _, ref_id = loaded_store

    async def fake_run(self: BaseAgent, payload):  # type: ignore[no-untyped-def]
        text = CANNED[self.prompt_name].replace("__FIRST__", ref_id)
        return self._parse(text)

    monkeypatch.setattr(BaseAgent, "run", fake_run)


@pytest.mark.asyncio
async def test_run_write_emits_full_event_sequence(loaded_store) -> None:
    store, set_id, _ = loaded_store
    request = WriteRequest(
        topic="CRISPR off-target effects",
        set_id=set_id,
        sections=[SectionName.INTRODUCTION, SectionName.METHODS, SectionName.DISCUSSION],
    )

    events = []
    async for ev in write_module.run_write(request, store=store):
        events.append(ev)

    kinds = [e.kind for e in events]
    assert kinds[0] == "started"
    assert kinds[-1] == "completed"
    assert kinds.count("section_started") == 3
    assert kinds.count("section_completed") == 3
    assert "references_formatted" in kinds
    assert "paper_assembled" in kinds
    assert "review_completed" in kinds

    final = events[-1].payload
    md = final["paper"]["markdown"]
    assert "[1]" in md  # citation marker rewritten
    assert "[ref=" not in md  # raw markers replaced
    assert "## Introduction" in md
    assert "## Methods" in md
    assert "## Discussion" in md
    assert "## Abstract" not in md  # not requested
    assert final["review"]["synthesis"]["top_revisions"]


@pytest.mark.asyncio
async def test_run_write_unknown_set_returns_error_event(loaded_store) -> None:
    store, _, _ = loaded_store
    request = WriteRequest(
        topic="missing set", set_id="does-not-exist", sections=[SectionName.METHODS]
    )
    events = [ev async for ev in write_module.run_write(request, store=store)]
    assert events[-1].kind == "error"


@pytest.mark.asyncio
async def test_run_write_skip_review_omits_review_events(loaded_store) -> None:
    store, set_id, _ = loaded_store
    request = WriteRequest(
        topic="skip review topic", set_id=set_id, sections=[SectionName.METHODS]
    )
    events = [
        ev async for ev in write_module.run_write(request, store=store, skip_review=True)
    ]
    kinds = [e.kind for e in events]
    assert "review_started" not in kinds
    assert "review_completed" not in kinds
    assert events[-1].payload["review"] is None
