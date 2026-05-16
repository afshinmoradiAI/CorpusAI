# CorpusAI — Academic Multi-Agent Assistant
 
## What this is
A web app that generates academic research papers section by section
using a team of specialised AI agents. The user provides a topic and
parameters; the system returns a paper with Abstract, Introduction,
Methods, Results, Discussion, and References.
 
## Stack
- Backend:  Python 3.11, FastAPI, PydanticAI (pydantic-ai-slim[anthropic])
- Frontend: Next.js 14 (App Router), TypeScript, Tailwind
- LLM:      Anthropic Claude via PydanticAI's AnthropicModel/AnthropicProvider
- Package manager (Python): uv
- Package manager (Node):   npm
- Shell:    Git Bash on Windows ARM64
 
## Architecture (today)
Monolith. One FastAPI service, one Next.js app. Agents live in
backend/app/agents/. Each agent has a .py class and a .md prompt
file in backend/app/prompts/. Four async generator workflows
coordinate agents without a graph library:
- explore.py — topic → web search → summarise → gap → idea → method
  → discussion. Used for the "Proposal" mode.
- write.py   — uploaded PDFs → section writers (Abstract → Introduction
  → Methods → Results → Discussion → References), then runs
  BiologyReviewer, StatisticsReviewer, and GapReviewer in parallel,
  then ReviewSynthesiser on the merged feedback. Used for the
  "Scientific Paper" mode.
- nhmrc.py   — topic (+ optional uploaded PDFs) → Burden of Disease
  → Aims & Hypotheses → Methods → Consumer & Community Involvement
  → Significance & Impact → Synopsis (written last). Used for the
  "NHMRC Grant" mode. Supports all NHMRC schemes (Ideas, Investigator,
  Synergy, Partnership, Clinical Trial, Postgraduate).
- arc.py     — topic (+ optional uploaded PDFs) → Significance
  → Innovation → Aims → Approach & Methodology → National Benefit
  → Project Description (written last, placed first). Used for the
  "ARC Grant" mode. Supports all ARC schemes (Discovery, Linkage,
  Laureate, DECRA, Future, Centre of Excellence) and the four
  innovation types (conceptual, methodological, empirical, integrative).
- thesis.py  — title + 1–15 chapters → per-chapter generation (each
  optionally grounded in its own PDFs + figures) → ThesisAbstractWriter
  synthesises the final abstract last. Used for the "Thesis" mode.
  Chapter titles auto-fill by position (Chapter 1 = Introduction,
  Chapter N = Conclusion, middle chapters cycle through Lit Review /
  Methodology / Results / Discussion).

Figures (Thesis only): users upload images per chapter via
POST /api/thesis/upload-figure. The writer emits `[fig=ID]` inline
references and `<<FIG=ID>>` block markers; the assembler renumbers
them globally as "Figure N" + markdown image embeds; the DOCX
exporter resolves figure IDs through services/figure_store.py and
calls doc.add_picture() at marker positions.

DOCX export (services/docx_export.py) is shared by all modes — it
converts the assembled markdown into a Times New Roman .docx file,
embedding figures when it encounters `![Figure N](/api/thesis/figure/ID)`
markdown.
 
## Conventions
- Every agent inherits from BaseAgent in agents/base.py
- BaseAgent wraps a PydanticAI Agent (lazy-constructed in _get_agent())
- Prompts live in prompts/*.md — never hardcode prompts in Python
- All agent I/O uses Pydantic models from schemas/
- Async everywhere on the backend
- Type hints on every public function
- Do NOT instantiate AnthropicModel or Agent outside of BaseAgent —
  the base class handles retries (tenacity), prompt caching, and usage accounting
 
## How to run
- Backend:  cd backend && uv run uvicorn app.main:app --reload
- Frontend: cd frontend && npm run dev
- Tests:    cd backend && uv run pytest
 
## Things you should never do
- Don't hardcode API keys — use .env
- Don't change the BaseAgent contract without updating all subclasses
- Don't commit CLAUDE.local.md or .env
- Don't let agents call each other directly — go through the Workflow
- Don't skip writing a test when adding a new agent
- Don't push directly to main — use a feature branch
 
## See also
- .claude/rules/agent-conventions.md
- .claude/rules/api-conventions.md
