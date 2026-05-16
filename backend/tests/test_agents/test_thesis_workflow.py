"""End-to-end tests for the Thesis workflow with all LLM calls mocked.

Covers:
- A topic-only thesis (no PDFs, no figures) generates N chapters + abstract.
- Auto-titles fill in for chapters that omit a title.
- Figure markers (`[fig=ID]` inline + `<<FIG=ID>>` block) get renumbered
  globally and rewritten into the markdown image embed + caption.
- An unknown set_id on any chapter aborts with an error event.
"""

from __future__ import annotations

import io

import pytest
from reportlab.pdfgen import canvas  # type: ignore[import-untyped]

from app.agents.base import BaseAgent
from app.schemas.thesis import (
    ChapterConfig,
    FigureRef,
    ThesisRequest,
    ThesisStructure,
    auto_chapter_title,
)
from app.services.reference_store import ReferenceStore
from app.workflows import thesis as thesis_module


def _pdf(text: str) -> bytes:
    buf = io.BytesIO()
    c = canvas.Canvas(buf)
    c.drawString(72, 720, text)
    c.showPage()
    c.save()
    return buf.getvalue()


CANNED: dict[str, str] = {
    "thesis_chapter_writer": (
        '{"content":"This chapter discusses the topic. '
        'As shown in [fig=FIG_A], the data is clear.\\n\\n<<FIG=FIG_A>>\\n\\n'
        'See excerpt [ref=__FIRST__]."}'
    ),
    "thesis_abstract_writer": (
        '{"content":"This thesis investigates X using Y and finds Z."}'
    ),
    "reference_formatter": (
        '{"references":[{"ref_id":"__FIRST__","citation":"Doe J. (2024). Title. Journal."}]}'
    ),
}


@pytest.fixture
async def loaded_store(tmp_path) -> tuple[ReferenceStore, str, str]:
    store = ReferenceStore(tmp_path / "thesis.sqlite")
    pdf = _pdf("Thesis reference content. " * 50)
    meta = await store.create_set([("source.pdf", pdf)])
    return store, meta.set_id, meta.documents[0].ref_id


@pytest.fixture
def _patch_llm(monkeypatch: pytest.MonkeyPatch):
    def _install(ref_id: str | None) -> None:
        async def fake_run(self: BaseAgent, payload):  # type: ignore[no-untyped-def]
            template = CANNED[self.prompt_name]
            text = template.replace("__FIRST__", ref_id or "missing")
            return self._parse(text)

        monkeypatch.setattr(BaseAgent, "run", fake_run)

    return _install


def test_auto_chapter_title_anchors_intro_and_conclusion() -> None:
    assert auto_chapter_title(1, 6).endswith("Introduction")
    assert auto_chapter_title(6, 6).endswith("Conclusion")
    assert auto_chapter_title(1, 1).endswith("Introduction")
    middle = auto_chapter_title(3, 6)
    assert "Chapter 3:" in middle
    assert middle.split(": ")[1] in {
        "Literature Review",
        "Methodology",
        "Results",
        "Discussion",
    }


@pytest.mark.asyncio
async def test_thesis_with_pdfs_and_figures_emits_full_sequence(
    loaded_store, _patch_llm
) -> None:
    store, set_id, ref_id = loaded_store
    _patch_llm(ref_id)

    request = ThesisRequest(
        title="Mitochondrial dynamics in T-cell exhaustion",
        discipline="Immunology",
        structure=ThesisStructure.TRADITIONAL,
        chapters=[
            ChapterConfig(
                title=None,  # auto -> Introduction
                notes="Set scope and aims.",
                set_id=set_id,
                figures=[
                    FigureRef(figure_id="FIG_A", caption="Overview schematic")
                ],
            ),
            ChapterConfig(
                title="Custom Methods Chapter",
                notes="Describe the assay.",
                set_id=set_id,
                figures=[],
            ),
            ChapterConfig(
                title=None,  # auto -> Conclusion (3rd of 3)
                notes=None,
                set_id=None,
                figures=[],
            ),
        ],
    )

    events = [ev async for ev in thesis_module.run_thesis(request, store=store)]
    kinds = [e.kind for e in events]

    assert kinds[0] == "started"
    assert kinds[-1] == "completed"
    assert kinds.count("chapter_started") == 3
    assert kinds.count("chapter_completed") == 3
    assert "abstract_started" in kinds
    assert "abstract_completed" in kinds
    assert "references_formatted" in kinds  # at least one chapter had a set_id
    assert "thesis_assembled" in kinds

    final = events[-1].payload["thesis"]
    md = final["markdown"]

    # Auto-titles applied where blank.
    assert "## Chapter 1: Introduction" in md
    assert "## Custom Methods Chapter" in md
    assert "## Chapter 3: Conclusion" in md

    # Figure markers rewritten globally.
    assert "[fig=" not in md
    assert "<<FIG=" not in md
    assert "Figure 1" in md
    assert "![Figure 1](/api/thesis/figure/FIG_A)" in md
    assert "**Figure 1.** Overview schematic" in md

    # Citation markers rewritten.
    assert "[ref=" not in md
    assert "[1]" in md
    assert "## References" in md


@pytest.mark.asyncio
async def test_thesis_topic_only_skips_references(_patch_llm, tmp_path) -> None:
    _patch_llm(None)
    store = ReferenceStore(tmp_path / "empty-thesis.sqlite")

    request = ThesisRequest(
        title="A short thesis with no uploads",
        structure=ThesisStructure.BY_PUBLICATION,
        chapters=[
            ChapterConfig(title=None, notes="Intro chapter."),
            ChapterConfig(title=None, notes="Conclusion chapter."),
        ],
    )

    events = [ev async for ev in thesis_module.run_thesis(request, store=store)]
    kinds = [e.kind for e in events]
    assert kinds[0] == "started"
    assert kinds[-1] == "completed"
    assert "references_formatted" not in kinds
    md = events[-1].payload["thesis"]["markdown"]
    assert "## References" not in md
    assert "## Abstract" in md


@pytest.mark.asyncio
async def test_thesis_unknown_set_id_aborts(loaded_store, _patch_llm) -> None:
    store, _, ref_id = loaded_store
    _patch_llm(ref_id)
    request = ThesisRequest(
        title="Bad set_id thesis",
        chapters=[ChapterConfig(set_id="does-not-exist")],
    )
    events = [ev async for ev in thesis_module.run_thesis(request, store=store)]
    assert events[-1].kind == "error"
