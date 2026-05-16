"""End-to-end tests for the ARC grant workflow with all LLM calls mocked.

Covers:
- A topic-only run (no uploaded PDFs) emits every section without references.
- A run with uploaded PDFs grounds each section and rewrites [ref=ID] markers
  into numbered citations.
- An unknown set_id yields an error event.
- One writer's render_input threads the scheme + innovation type + discipline.
"""

from __future__ import annotations

import io

import pytest
from reportlab.pdfgen import canvas  # type: ignore[import-untyped]

from app.agents.arc_writers import ARCSignificanceWriter
from app.agents.base import BaseAgent
from app.schemas.arc import (
    ARCRequest,
    ARCScheme,
    ARCSectionDraft,
    ARCSectionName,
    ARCWriterInput,
    CANONICAL_ARC_ORDER,
    InnovationType,
)
from app.services.reference_store import ReferenceStore
from app.workflows import arc as arc_module


CANNED: dict[str, str] = {
    "arc_opening_writer": '{"content":"We will determine X under Y. The project resolves a long-standing disagreement [ref=__FIRST__]."}',
    "arc_aims_writer": '{"content":"**Aim 1:** Quantify the contribution of grain boundaries to fatigue."}',
    "arc_significance_writer": '{"content":"Current models cannot explain Z [ref=__FIRST__]. This project will identify the mechanism."}',
    "arc_innovation_writer": '{"content":"The innovation is methodological: we apply technique X to problem Y."}',
    "arc_approach_writer": '{"content":"Aim 1 — We will sample 60 units. Risk: low yield; mitigation: alternative protocol."}',
    "arc_benefit_writer": '{"content":"Australia\'s additive manufacturing sector ($4.2B) gains certification data."}',
    "reference_formatter": (
        '{"references":[{"ref_id":"__FIRST__","citation":"Smith J. (2024). Title. Journal."}]}'
    ),
}


def _pdf(text: str) -> bytes:
    buf = io.BytesIO()
    c = canvas.Canvas(buf)
    c.drawString(72, 720, text)
    c.showPage()
    c.save()
    return buf.getvalue()


@pytest.fixture
async def loaded_store(tmp_path) -> tuple[ReferenceStore, str, str]:
    store = ReferenceStore(tmp_path / "arc.sqlite")
    pdf = _pdf("Grain boundary effects in additively manufactured titanium. " * 50)
    meta = await store.create_set([("paper1.pdf", pdf)])
    return store, meta.set_id, meta.documents[0].ref_id


@pytest.fixture
async def empty_store(tmp_path) -> ReferenceStore:
    return ReferenceStore(tmp_path / "empty-arc.sqlite")


@pytest.fixture
def _patch_llm(monkeypatch: pytest.MonkeyPatch):
    def _install(ref_id: str | None) -> None:
        async def fake_run(self: BaseAgent, payload):  # type: ignore[no-untyped-def]
            template = CANNED[self.prompt_name]
            text = template.replace("__FIRST__", ref_id or "missing")
            return self._parse(text)

        monkeypatch.setattr(BaseAgent, "run", fake_run)

    return _install


@pytest.mark.asyncio
async def test_run_arc_with_pdfs_emits_full_sequence_and_rewrites_refs(
    loaded_store, _patch_llm
) -> None:
    store, set_id, ref_id = loaded_store
    _patch_llm(ref_id)

    request = ARCRequest(
        topic="Quantifying grain boundary fatigue in additively manufactured Ti-6Al-4V",
        scheme=ARCScheme.DISCOVERY,
        innovation_type=InnovationType.METHODOLOGICAL,
        set_id=set_id,
        discipline="Materials engineering",
    )

    events = [ev async for ev in arc_module.run_arc(request, store=store)]
    kinds = [e.kind for e in events]

    assert kinds[0] == "started"
    assert kinds[-1] == "completed"
    assert kinds.count("section_started") == len(CANONICAL_ARC_ORDER)
    assert kinds.count("section_completed") == len(CANONICAL_ARC_ORDER)
    assert "references_formatted" in kinds
    assert "grant_assembled" in kinds

    final_md = events[-1].payload["grant"]["markdown"]
    assert "[1]" in final_md
    assert "[ref=" not in final_md
    assert "## Project Description" in final_md
    assert "## Significance" in final_md
    assert "## Innovation" in final_md
    assert "## Approach and Methodology" in final_md
    assert "## National Benefit" in final_md
    assert "## References" in final_md


@pytest.mark.asyncio
async def test_run_arc_without_pdfs_skips_references(
    empty_store, _patch_llm
) -> None:
    _patch_llm(None)

    request = ARCRequest(
        topic="Topic-only ARC run",
        scheme=ARCScheme.DECRA,
        innovation_type=InnovationType.CONCEPTUAL,
    )

    events = [ev async for ev in arc_module.run_arc(request, store=empty_store)]
    kinds = [e.kind for e in events]

    assert kinds[0] == "started"
    assert kinds[-1] == "completed"
    assert "references_formatted" not in kinds
    assert kinds.count("section_completed") == len(CANONICAL_ARC_ORDER)

    final_md = events[-1].payload["grant"]["markdown"]
    assert "## References" not in final_md
    assert "[ref=" not in final_md


@pytest.mark.asyncio
async def test_run_arc_unknown_set_returns_error_event(
    loaded_store, _patch_llm
) -> None:
    store, _, ref_id = loaded_store
    _patch_llm(ref_id)
    request = ARCRequest(
        topic="missing set",
        scheme=ARCScheme.DISCOVERY,
        innovation_type=InnovationType.METHODOLOGICAL,
        set_id="does-not-exist",
    )
    events = [ev async for ev in arc_module.run_arc(request, store=store)]
    assert events[-1].kind == "error"


@pytest.mark.asyncio
async def test_significance_writer_renders_scheme_and_discipline(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, str] = {}

    async def fake_run(self: BaseAgent, payload):  # type: ignore[no-untyped-def]
        captured["message"] = self.render_input(payload)
        return self._parse('{"content":"draft significance"}')

    monkeypatch.setattr(BaseAgent, "run", fake_run)

    agent = ARCSignificanceWriter()
    out = await agent.run(
        ARCWriterInput(
            topic="Bilingual statistical learning",
            scheme=ARCScheme.LAUREATE,
            innovation_type=InnovationType.INTEGRATIVE,
            section=ARCSectionName.SIGNIFICANCE,
            discipline="Cognitive science",
            notes="Cite Saffran et al. 1996.",
        )
    )

    assert isinstance(out, ARCSectionDraft)
    message = captured["message"]
    assert "ARC scheme: laureate" in message
    assert "Innovation type: integrative" in message
    assert "Cognitive science" in message
    assert "Saffran" in message
