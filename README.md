# CorpusAI

A multi-agent academic writing assistant. **Five pipelines, one app:**

- **Explore** — give it a topic; it surveys the literature, finds the gap, proposes an idea, designs a method, and writes a discussion.
- **Write** — upload reference PDFs; it drafts a full paper (Abstract / Introduction / Methods / Results / Discussion), formats citations, and runs a three-way peer review (biology, statistics, gap).
- **NHMRC Grant** — generates a full NHMRC grant application (Burden of Disease → Aims → Methods → Consumer Involvement → Impact → Synopsis). All NHMRC schemes supported.
- **ARC Grant** — generates a full ARC grant application (Significance → Innovation → Aims → Approach → National Benefit → Project Description). All ARC schemes + four innovation types.
- **Thesis** — define 1–15 chapters with optional per-chapter notes, reference PDFs, and figures. Each chapter is drafted in turn, then an abstract is synthesised. Figures embed inline in both the markdown preview and the .docx export.

All five pipelines export to **Times New Roman .docx**. Built on FastAPI + PydanticAI + Next.js + Claude.

```
┌────────────────────┐      ┌───────────────────────────┐      ┌─────────────────────┐
│  Next.js frontend  │ ───▶ │  FastAPI + 26 agents      │ ───▶ │  Anthropic Claude   │
│  (Vercel, free)    │      │  (Fly.io, ~$5/mo + vol)   │      │  (Sonnet 4.6)       │
└────────────────────┘      └───────────────────────────┘      └─────────────────────┘
                                       │
                                       ▼
                            ┌──────────────────────┐
                            │  SQLite + BM25 index │
                            │  + figure store      │
                            │  (Fly volume, 1 GB)  │
                            └──────────────────────┘
```

---

## Quick start (local)

**Backend:**

```bash
cd backend
cp .env.example .env            # add your ANTHROPIC_API_KEY
uv sync
uv run uvicorn app.main:app --reload
```

**Frontend:**

```bash
cd frontend
cp .env.local.example .env.local
npm install
npm run dev
```

Open <http://localhost:3000> and click **Settings** to paste your API key (if you set `APP_API_KEY` in the backend). You'll see five tabs across the top — pick the one you want.

**Tests + lint:**

```bash
cd backend && uv run pytest -q && uv run ruff check .
cd frontend && npx tsc --noEmit
```

---

## Pre-flight checklist (before deploying)

Run these from the repo root. All four should pass before `fly deploy`.

```bash
# 1. Backend tests + lint
cd backend && uv run pytest -q && uv run ruff check . && cd ..

# 2. Frontend type check
cd frontend && npx tsc --noEmit && cd ..

# 3. Production Docker image builds
docker build -t corpusai-test backend/

# 4. Commit everything (git status should be clean)
git status
```

Then make sure these are in place:

- [ ] `ANTHROPIC_API_KEY` — your Claude API key
- [ ] `APP_API_KEY` — strong random secret (`python -c "import secrets; print(secrets.token_urlsafe(32))"`)
- [ ] `CORS_ALLOWED_ORIGINS` — your Vercel domain
- [ ] Fly volume created (`fly volumes create corpusai_data --size 1`)
- [ ] `fly.toml` mount points to `/data`
- [ ] Vercel env vars: `NEXT_PUBLIC_API_URL` + `NEXT_PUBLIC_API_KEY`

Full deploy steps in [DEPLOY.md](DEPLOY.md).

**MCP server** (optional — exposes paper search to other MCP clients):

```bash
cd backend && uv run python -m app.mcp_server
# → http://localhost:8765/mcp
```

---

## What's in the box

| Layer | Tech |
|---|---|
| Agents | 26 PydanticAI agents, each loading its prompt from `backend/app/prompts/*.md` |
| LLM | Claude Sonnet 4.6 via PydanticAI `AnthropicProvider` (prompt caching on) |
| Orchestration | Hand-written `asyncio` workflows in `backend/app/workflows/` (5 pipelines) |
| Retrieval | BM25 over chunked PDFs (`rank-bm25`) |
| Storage | SQLite (3 tables) + in-process LRU for BM25 indexes + on-disk figure store |
| API | FastAPI with SSE streaming, RFC 7807 errors, rate limiting, API-key auth |
| Export | Times New Roman .docx with embedded figures (`python-docx`) |
| Frontend | Next.js 14 App Router, Tailwind, SSE client, 5 mode tabs |
| Deployment | Fly.io (backend) + Vercel (frontend), ~$5/month |

---

## API surface

| Pipeline | Endpoint | Auth | Notes |
|---|---|---|---|
| Explore (proposal) | `POST /api/research/explore` | ✅ | SSE stream |
| Write (scientific paper) | `POST /api/paper/write` | ✅ | SSE stream; requires uploaded `set_id` |
| NHMRC grant | `POST /api/nhmrc/write` | ✅ | SSE stream |
| ARC grant | `POST /api/arc/write` | ✅ | SSE stream |
| Thesis | `POST /api/thesis/write` | ✅ | SSE stream |
| Upload PDFs | `POST /api/paper/upload-refs` | ✅ | Returns `set_id` |
| Upload figure | `POST /api/thesis/upload-figure` | ✅ | Returns `figure_id` |
| Serve figure | `GET /api/thesis/figure/{id}` | ❌ public | `<img>` can't send headers; UUID4 is the key |
| DOCX export | `POST /api/paper/export/docx` | ✅ | Times New Roman |

---

## Documentation

- **[TUTORIAL.md](TUTORIAL.md)** — guided walkthrough of every feature, grouped by category. Start here if you want to understand the codebase or learn the patterns.
- **[DEPLOY.md](DEPLOY.md)** — step-by-step Fly.io + Vercel deployment.
- **[CLAUDE.md](CLAUDE.md)** — conventions and rules the codebase follows.

---

## Repository layout

```
CorpusAI/
├── backend/
│   ├── app/
│   │   ├── agents/         # 26 agents inheriting from BaseAgent
│   │   │                   #   (writers, reviewers, NHMRC, ARC, thesis)
│   │   ├── api/            # FastAPI routes:
│   │   │                   #   routes_research, routes_papers,
│   │   │                   #   routes_nhmrc, routes_arc, routes_thesis
│   │   ├── core/           # config, logging, security, cache, usage, problem (RFC 7807)
│   │   ├── prompts/        # 30 .md prompt files (one per agent)
│   │   ├── schemas/        # Pydantic models (research, paper, nhmrc, arc, thesis)
│   │   ├── services/       # SQLite store, BM25 retrieval, Semantic Scholar,
│   │   │                   #   PDF reader, figure store, DOCX export
│   │   ├── workflows/      # explore.py, write.py, nhmrc.py, arc.py, thesis.py
│   │   ├── main.py         # FastAPI app + middleware
│   │   └── mcp_server.py   # MCP server exposing paper services
│   ├── tests/              # pytest suite (48 tests)
│   ├── fly.toml + Dockerfile
│   └── pyproject.toml
├── frontend/
│   ├── app/                # Next.js routes
│   ├── components/         # explore/, write/, nhmrc/, arc/, thesis/,
│   │                       #   ui/, SettingsDialog, ModeTabs
│   └── lib/                # api, auth, sse, types
├── .github/workflows/ci.yml
├── README.md / TUTORIAL.md / DEPLOY.md / CLAUDE.md
└── docker-compose.yml
```

---

## License

Private project. No license granted yet.
