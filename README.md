# CorpusAI

A multi-agent academic research assistant. Two pipelines, one app:

- **Explore** — give it a topic; it surveys the literature, finds the gap, proposes an idea, designs a method, and writes a discussion.
- **Write** — upload reference PDFs; it drafts a full paper (Abstract / Introduction / Methods / Results / Discussion), formats citations, and runs a three-way peer review (biology, statistics, gap).

Built on FastAPI + PydanticAI + Next.js + Claude.

```
┌────────────────────┐      ┌───────────────────────────┐      ┌─────────────────────┐
│  Next.js frontend  │ ───▶ │  FastAPI + 18 agents      │ ───▶ │  Anthropic Claude   │
│  (Vercel, free)    │      │  (Fly.io, ~$5/mo + vol)   │      │  (Sonnet 4.6)       │
└────────────────────┘      └───────────────────────────┘      └─────────────────────┘
                                       │
                                       ▼
                            ┌──────────────────────┐
                            │  SQLite + BM25 index │
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

Open <http://localhost:3000> and click **Settings** to paste your API key (if you set `APP_API_KEY` in the backend).

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
| Agents | 18 PydanticAI agents, each loading its prompt from `backend/app/prompts/*.md` |
| LLM | Claude Sonnet 4.6 via PydanticAI `AnthropicProvider` (prompt caching on) |
| Orchestration | Hand-written `asyncio` workflows in `backend/app/workflows/` |
| Retrieval | BM25 over chunked PDFs (`rank-bm25`) |
| Storage | SQLite (3 tables) + in-process LRU for BM25 indexes |
| API | FastAPI with SSE streaming, RFC 7807 errors, rate limiting, API-key auth |
| Frontend | Next.js 14 App Router, Tailwind, SSE client |
| Deployment | Fly.io (backend) + Vercel (frontend), ~$5/month |

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
│   │   ├── agents/         # 18 agents inheriting from BaseAgent
│   │   ├── api/            # FastAPI routes (research, paper)
│   │   ├── core/           # config, logging, security, cache, usage, problem (RFC 7807)
│   │   ├── prompts/        # 17 .md prompt files (one per agent)
│   │   ├── schemas/        # Pydantic models
│   │   ├── services/       # SQLite store, BM25 retrieval, Semantic Scholar, PDF reader
│   │   ├── workflows/      # explore.py, write.py (the orchestrators)
│   │   ├── main.py         # FastAPI app + middleware
│   │   └── mcp_server.py   # MCP server exposing paper services
│   ├── tests/              # pytest suite (28 tests)
│   ├── fly.toml + Dockerfile
│   └── pyproject.toml
├── frontend/
│   ├── app/                # Next.js routes
│   ├── components/         # explore/, write/, ui/, SettingsDialog, ModeTabs
│   └── lib/                # api, auth, sse, types
├── .github/workflows/ci.yml
├── README.md / TUTORIAL.md / DEPLOY.md / CLAUDE.md
└── docker-compose.yml
```

---

## License

Private project. No license granted yet.
