"""End-to-end tests for the NHMRC grant workflow with all LLM calls mocked.

Covers:
- A topic-only run (no uploaded PDFs) emits every section without references.
- A run with uploaded PDFs grounds each section and rewrites [ref=ID] markers
  into numbered citations.
- An unknown set_id yields an error event.
- One agent's render_input correctly threads the scheme + study type + notes.
"""

from __future__ import annotations

import io

import pytest
from reportlab.pdfgen import canvas  # type: ignore[import-untyped]

from app.agents.base import BaseAgent
from app.agents.nhmrc_writers import BurdenOfDiseaseWriter
from app.schemas.nhmrc import (
    CANONICAL_NHMRC_ORDER,
    NHMRCRequest,
    NHMRCScheme,
    NHMRCSectionDraft,
    NHMRCSectionName,
    NHMRCWriterInput,
    StudyType,
)
from app.services.reference_store import ReferenceStore
from app.workflows import nhmrc as nhmrc_module


CANNED: dict[str, str] = {
    "nhmrc_synopsis_writer": '{"content":"One in 20 Australians live with X. Plain-language synopsis [ref=__FIRST__]."}',
    "nhmrc_burden_writer": '{"content":"Condition affects 1.3 million Australians [ref=__FIRST__]."}',
    "nhmrc_aims_writer": '{"content":"**Aim 1:** Determine effect. Hypothesis: ≥50% reduction."}',
    "nhmrc_methods_writer": '{"content":"### Design\\nMulti-centre RCT, 320 adults [ref=__FIRST__]."}',
    "nhmrc_consumer_writer": '{"content":"Two consumer co-investigators co-designed the trial."}',
    "nhmrc_impact_writer": '{"content":"RACGP will assess for the Red Book within 12 months."}',
    "reference_formatter": (
        '{"references":[{"ref_id":"__FIRST__","citation":"AIHW (2023). Australian Health Report."}]}'
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
    store = ReferenceStore(tmp_path / "nhmrc.sqlite")
    pdf = _pdf("Burden of treatment-resistant depression in Australia. " * 50)
    meta = await store.create_set([("paper1.pdf", pdf)])
    return store, meta.set_id, meta.documents[0].ref_id


@pytest.fixture
async def empty_store(tmp_path) -> ReferenceStore:
    return ReferenceStore(tmp_path / "empty-nhmrc.sqlite")


@pytest.fixture
def _patch_llm(monkeypatch: pytest.MonkeyPatch):
    """Route every BaseAgent.run by prompt name to a canned reply.

    Returns a closure that callers can use to inject the live ref_id into
    the `__FIRST__` placeholder.
    """

    def _install(ref_id: str | None) -> None:
        async def fake_run(self: BaseAgent, payload):  # type: ignore[no-untyped-def]
            template = CANNED[self.prompt_name]
            text = template.replace("__FIRST__", ref_id or "missing")
            return self._parse(text)

        monkeypatch.setattr(BaseAgent, "run", fake_run)

    return _install


@pytest.mark.asyncio
async def test_run_nhmrc_with_pdfs_emits_full_sequence_and_rewrites_refs(
    loaded_store, _patch_llm
) -> None:
    store, set_id, ref_id = loaded_store
    _patch_llm(ref_id)

    request = NHMRCRequest(
        topic="Targeted T-cell therapy for treatment-resistant depression",
        scheme=NHMRCScheme.IDEAS,
        study_type=StudyType.CLINICAL_TRIAL,
        set_id=set_id,
        health_condition="Treatment-resistant depression",
        target_population="Australian adults 18-65",
    )

    events = [ev async for ev in nhmrc_module.run_nhmrc(request, store=store)]
    kinds = [e.kind for e in events]

    assert kinds[0] == "started"
    assert kinds[-1] == "completed"
    # Six sections each emit started + completed.
    assert kinds.count("section_started") == len(CANONICAL_NHMRC_ORDER)
    assert kinds.count("section_completed") == len(CANONICAL_NHMRC_ORDER)
    assert "references_formatted" in kinds
    assert "grant_assembled" in kinds

    final_md = events[-1].payload["grant"]["markdown"]
    assert "[1]" in final_md  # citation marker rewritten
    assert "[ref=" not in final_md  # raw markers replaced
    assert "## Burden of Disease" in final_md
    assert "## Research Plan / Methods" in final_md
    assert "## Synopsis" in final_md
    assert "## References" in final_md


@pytest.mark.asyncio
async def test_run_nhmrc_without_pdfs_skips_references(
    empty_store, _patch_llm
) -> None:
    _patch_llm(None)

    request = NHMRCRequest(
        topic="Topic-only run without a reference set",
        scheme=NHMRCScheme.INVESTIGATOR,
        study_type=StudyType.LABORATORY,
        set_id=None,
    )

    events = [ev async for ev in nhmrc_module.run_nhmrc(request, store=empty_store)]
    kinds = [e.kind for e in events]

    assert kinds[0] == "started"
    assert kinds[-1] == "completed"
    assert "references_formatted" not in kinds  # no PDFs => no formatter call
    assert kinds.count("section_completed") == len(CANONICAL_NHMRC_ORDER)

    final_md = events[-1].payload["grant"]["markdown"]
    assert "## References" not in final_md
    # Unmatched [ref=__FIRST__] markers should still get replaced to [?].
    assert "[ref=" not in final_md


@pytest.mark.asyncio
async def test_run_nhmrc_unknown_set_returns_error_event(
    loaded_store, _patch_llm
) -> None:
    store, _, ref_id = loaded_store
    _patch_llm(ref_id)
    request = NHMRCRequest(
        topic="missing set",
        scheme=NHMRCScheme.IDEAS,
        study_type=StudyType.LABORATORY,
        set_id="does-not-exist",
    )
    events = [ev async for ev in nhmrc_module.run_nhmrc(request, store=store)]
    assert events[-1].kind == "error"


@pytest.mark.asyncio
async def test_burden_writer_renders_scheme_and_notes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, str] = {}

    async def fake_run(self: BaseAgent, payload):  # type: ignore[no-untyped-def]
        captured["message"] = self.render_input(payload)
        return self._parse('{"content":"draft burden statement"}')

    monkeypatch.setattr(BaseAgent, "run", fake_run)

    agent = BurdenOfDiseaseWriter()
    out = await agent.run(
        NHMRCWriterInput(
            topic="Diabetes equity",
            scheme=NHMRCScheme.PARTNERSHIP,
            study_type=StudyType.OBSERVATIONAL,
            section=NHMRCSectionName.BURDEN,
            health_condition="Type 2 diabetes",
            target_population="Aboriginal and Torres Strait Islander adults",
            notes="Co-led with Wuchopperen Health Service.",
        )
    )

    assert isinstance(out, NHMRCSectionDraft)
    message = captured["message"]
    assert "NHMRC scheme: partnership" in message
    assert "Study type: observational" in message
    assert "Type 2 diabetes" in message
    assert "Wuchopperen" in message
