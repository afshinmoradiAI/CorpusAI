# CorpusAI Tutorial

A learning-oriented tour of every feature in this app, grouped by category. Each entry tells you **what it is**, **why it matters**, **where to find it in the code**, and (where relevant) **what alternatives were considered**.

If you're new to the codebase, read this top-to-bottom — it doubles as a map of the system. End with the [Real gaps](#real-gaps-if-strangers-use-it) section to know what's still missing.

---

## 1. Agent framework

### PydanticAI
- **What:** Type-safe wrapper for LLM agents. Every agent returns a validated Pydantic model — no manual JSON parsing.
- **Why:** Agents naturally produce structured output; PydanticAI enforces it. Less boilerplate than the Anthropic SDK, smaller than LangChain, and **MCP is first-class**.
- **Where:** [`backend/app/agents/base.py`](backend/app/agents/base.py). All 26 agents inherit from `BaseAgent` and only need to declare `prompt_name`, `output_model`, and a `render_input()` method.
- **Alternatives considered:** Microsoft Agent Framework (was here originally — added almost no value, only wrapped the SDK), LangGraph (too heavy), raw Anthropic SDK (more boilerplate, no MCP).

### BaseAgent contract
- Subclasses declare:
  - `prompt_name: str` — file in `prompts/<name>.md`
  - `output_model: type[BaseModel]` — Pydantic class the agent must return
  - `render_input(payload) -> str` — turn typed input into the user message
- Agents never call each other. Workflows in `workflows/` orchestrate them.

### Prompts on disk
- **What:** Every system prompt lives in `backend/app/prompts/*.md`, loaded via `load_prompt()`.
- **Why:** Prompts are content, not code. Editing them shouldn't require redeploying Python.
- **Where:** [`backend/app/core/prompts.py`](backend/app/core/prompts.py).

---

## 2. Security

### API-key authentication
- **What:** Every route under `/api/*` requires an `X-API-Key` header matching `APP_API_KEY`.
- **Why:** Without auth, anyone could burn your Anthropic credits. A shared key is the cheapest gate; if `APP_API_KEY` is unset, auth is bypassed (dev mode).
- **Where:** [`backend/app/core/security.py`](backend/app/core/security.py) (the `verify_api_key` dependency), wired in [`main.py`](backend/app/main.py).

### Per-user scoping
- **What:** Optional `X-User-ID` header. Uploaded PDFs are stored against the caller; other users can't read them by guessing the `set_id`.
- **Why:** Without scoping, every user with the shared API key sees every set. With it, multiple people can use one deployment safely-ish.
- **Where:** [`security.py:current_user_id`](backend/app/core/security.py), enforced in [`reference_store.py:_check_owner`](backend/app/services/reference_store.py).
- **Caveat:** The user_id is trusted from the header. This is **not real auth** — see the [Real gaps](#real-gaps-if-strangers-use-it) section.

### Rate limiting
- **What:** `slowapi` middleware caps requests per IP. Default: 10/minute.
- **Why:** A single malicious user could otherwise trigger hundreds of concurrent Explore runs ($$$).
- **Where:** [`main.py`](backend/app/main.py) (`Limiter` setup), configurable via `RATE_LIMIT_PER_MINUTE`.

### Input validation
- **What:** Pydantic field constraints on every request body — `min_length`, `max_length`, etc.
- **Why:** Prompt-injection mitigation + sanity caps so a 10MB topic string doesn't reach Claude.
- **Where:** `schemas/research.py` and `schemas/paper.py`.

### File upload limits
- **What:** Max 30 PDF files per request, max 25 MB per file, `.pdf` extension only.
- **Why:** Avoid OOM and storage-exhaustion attacks.
- **Where:** [`routes_papers.py:upload_refs`](backend/app/api/routes_papers.py).

### Scrubbed health endpoint
- **What:** `/health` returns only `{"status": "ok"}` — no model name, no key status, no version info.
- **Why:** The health endpoint is the easiest thing to scrape; it shouldn't leak system info.

---

## 3. Errors & observability

### RFC 7807 problem details
- **What:** All errors return `application/problem+json` with `{type, title, status, detail, instance}`.
- **Why:** Standardised, machine-readable error responses. Your `CLAUDE.md` already required this.
- **Where:** [`backend/app/core/problem.py`](backend/app/core/problem.py), wired in `main.py`.

### Structured logging (structlog)
- **What:** JSON logs in production, pretty console in dev. Every log line carries `request_id`, `path`, `method`.
- **Why:** Grepping by `request_id` lets you trace a single user's failure end-to-end.
- **Where:** [`backend/app/core/logging.py`](backend/app/core/logging.py).

### Request-ID propagation
- **What:** Middleware accepts or generates `X-Request-ID`, binds it to structlog context, and echoes it back to the client.
- **Why:** Frontend can include the request_id in bug reports; logs let you find that exact call.
- **Where:** [`main.py:RequestContextMiddleware`](backend/app/main.py).

### Per-agent usage logging
- **What:** Every agent call logs input/output/cache tokens after running.
- **Why:** Lets you see which agents are expensive and which benefit from caching.
- **Where:** [`base.py:_record_usage`](backend/app/agents/base.py).

### Retry on transient Anthropic failures
- **What:** Every agent call is wrapped in `tenacity` retry with exponential backoff + jitter. Retries on `RateLimitError`, `APITimeoutError`, and `APIStatusError` with status 429/5xx. Up to 4 attempts. Caller errors (4xx other than 429) are not retried.
- **Why:** A single transient blip in the Anthropic API used to fail a 60-second Write workflow and waste all prior work. Retries make the system resilient to brief upstream incidents.
- **Where:** [`base.py:_run_with_retries`](backend/app/agents/base.py). Each retry attempt is logged at WARNING.

### Cost visibility (`usage` SSE event)
- **What:** Just before the final `completed` event, every workflow emits a `usage` event with `{input_tokens, output_tokens, cache_read_tokens, cache_write_tokens, requests, estimated_cost_usd, agent_breakdown}`.
- **Why:** Users used to have no idea how much a run cost. Now the frontend can display "this run used 47K tokens (~$0.15)" — builds trust and helps users self-throttle.
- **Where:** [`backend/app/core/usage.py:UsageScope.summary`](backend/app/core/usage.py), wired into both workflows. Pricing assumes Sonnet rates as a worst-case bound (Haiku agents are cheaper).

---

## 4. Memory & state

### SQLite persistent store
- **What:** Uploaded papers, documents, and chunks live in a SQLite file on a Fly volume. Survives restarts.
- **Why:** The original in-memory store lost everything on restart. SQLite is the smallest persistent option that supports the access pattern.
- **Where:** [`backend/app/services/reference_store.py`](backend/app/services/reference_store.py).
- **Schema:**
  - `ref_sets(set_id, user_id, created_at)` — one row per upload session
  - `documents(ref_id, set_id, filename, page_count, char_count)` — one per PDF
  - `chunks(chunk_id, set_id, ref_id, page, text)` — many per document
- **Alternatives considered:** Postgres (overkill for current scale), in-memory + S3 (more moving parts), Fly Postgres (extra cost).

### BM25 index (lazy, in-process)
- **What:** When a workflow needs to search a set, the store loads chunks from SQLite, builds a BM25 index in memory, and caches it in an LRU (max 32 sets).
- **Why:** BM25 needs token lists, not raw text. Rebuilding on every request would be wasteful; persisting the index would couple storage to the retrieval algorithm.
- **Where:** [`services/retrieval.py`](backend/app/services/retrieval.py) + [`reference_store.py:get_index`](backend/app/services/reference_store.py).
- **Alternative considered:** Embeddings + vector DB (overkill for 5–30 PDFs; BM25 is competitive on scientific text).

### Data deletion (GDPR)
- **What:** `DELETE /api/paper/refs/{set_id}` removes a set and all its documents + chunks. Foreign-key `ON DELETE CASCADE` does the heavy lifting; the in-memory BM25 cache is invalidated for that set.
- **Why:** Users must be able to delete their own data. Required for GDPR; basic decency for non-EU users too.
- **Where:** [`routes_papers.py:delete_ref_set`](backend/app/api/routes_papers.py) + [`reference_store.py:delete_set`](backend/app/services/reference_store.py). Ownership is enforced — Bob can't delete Alice's set.

---

## 5. Caching

### Anthropic prompt caching
- **What:** Each agent's system prompt is marked for caching. Repeat calls within 5 minutes pay ~10% of the input-token cost for the prompt.
- **Why:** All 26 agents have long static system prompts. After the first call, every subsequent call is ~70% cheaper on input.
- **Where:** [`base.py`](backend/app/agents/base.py): `AnthropicModelSettings(anthropic_cache_instructions=True)`.
- **Trade-off:** Caching costs 25% more on first write — so it only pays off if you call the same agent at least twice within 5 minutes. Workflows naturally do this.

### Workflow result cache (LRU)
- **What:** Identical Explore/Write requests return the cached result instantly. Keyed by SHA-256 of the normalised payload.
- **Why:** Users retry the same query; this saves the full $0.30–$0.60 each time.
- **Where:** [`backend/app/core/cache.py`](backend/app/core/cache.py), applied in `workflows/explore.py` and `write.py`.
- **Bounded:** `RESULT_CACHE_SIZE=64` recent results per pipeline. In-memory only — cleared on restart.

---

## 6. Cost control

### Per-request spend cap
- **What:** Each workflow runs inside a `usage_scope`. Every agent call adds its token counts to the scope; if the total exceeds `MAX_TOKENS_PER_REQUEST`, the workflow raises `SpendCapExceeded` and surfaces it as an SSE error.
- **Why:** A pathological topic could otherwise burn through a million tokens. Hard cap = hard budget.
- **Where:** [`backend/app/core/usage.py`](backend/app/core/usage.py), enforced in [`base.py:_record_usage`](backend/app/agents/base.py).
- **Mechanism:** `contextvars` — the scope is automatic for any agent call inside the workflow.

### Token budget reporting
- Successful workflows log `input_tokens`, `output_tokens`, `cache_read_tokens`, and `requests` at completion. Grep your logs to spot trends.

### Mixed-model strategy (Sonnet + Haiku)
- **What:** Each agent can declare its own `model = "claude-..."` class attribute. The default (`ANTHROPIC_CHAT_MODEL`) is Sonnet 4.6; three agents override to Haiku 4.5 (`ANTHROPIC_FAST_MODEL`):
  - `PaperSummariser` — extracts structured fields from an abstract
  - `TopicAnalyser` — generates keyword + sub-domain lists
  - `ReferenceFormatter` — emits APA-style citation strings
- **Why:** These tasks are mechanical extraction/formatting where Sonnet's reasoning is wasted. Haiku is ~5× cheaper per token with no measurable quality loss. The writers and reviewers (where reasoning matters) stay on Sonnet.
- **Where:** Each agent class sets `model = get_settings().anthropic_fast_model`. Config in [`core/config.py`](backend/app/core/config.py); plumbing in [`base.py:_get_agent`](backend/app/agents/base.py).
- **Net effect:** ~40% reduction in cost per Explore run (8 summariser calls, all now on Haiku).

---

## 7. Workflows & streaming

### Five pipelines, async generators
- `run_explore` — Topic → analyse → search → summarise (parallel) → gap → idea → method → discussion → done
- `run_write` — Set_id → 5 section writers (sequential) → format references → assemble paper → 3 reviewers (parallel) → synthesise → done
- `run_nhmrc` — Topic (+ optional PDFs) → Burden → Aims → Methods → Consumer Involvement → Impact → Synopsis (written last) → done. Supports all NHMRC schemes (Ideas, Investigator, Synergy, Partnership, Clinical Trial, Postgraduate) and five study types.
- `run_arc` — Topic (+ optional PDFs) → Significance → Innovation → Aims → Approach → National Benefit → Project Description (written last, placed first) → done. Supports all ARC schemes (Discovery, Linkage, Laureate, DECRA, Future, Centre) and four innovation types.
- `run_thesis` — Title + 1–15 chapters (each with optional notes/PDFs/figures) → chapter-by-chapter generation → ThesisAbstractWriter synthesises the abstract last → done. Chapter titles auto-fill by position (Chapter 1 = Introduction, last chapter = Conclusion, middle cycles through Literature Review / Methodology / Results / Discussion).
- **Where:** [`workflows/explore.py`](backend/app/workflows/explore.py), [`workflows/write.py`](backend/app/workflows/write.py), [`workflows/nhmrc.py`](backend/app/workflows/nhmrc.py), [`workflows/arc.py`](backend/app/workflows/arc.py), [`workflows/thesis.py`](backend/app/workflows/thesis.py).

### Figures (Thesis mode)
- **What:** Users upload images per chapter via `POST /api/thesis/upload-figure`. The writer is told which figures are available (with captions) and emits `[fig=ID]` inline references and `<<FIG=ID>>` block markers in its output. The assembler renumbers them globally (Figure 1, 2, …) using order-of-first-mention, replaces inline markers with `Figure N`, and replaces block markers with a markdown image embed + caption block.
- **Why:** Users want figures placed *where the chapter talks about them*, not at the end. Letting the LLM choose placement (via markers) keeps the writing natural; the assembler handles global numbering so the writer doesn't have to know what figure index it's at.
- **Where:** [`services/figure_store.py`](backend/app/services/figure_store.py) (on-disk store), [`workflows/thesis.py`](backend/app/workflows/thesis.py) (assembler logic), [`services/docx_export.py`](backend/app/services/docx_export.py) (resolves IDs and embeds pictures).
- **Public endpoint caveat:** `GET /api/thesis/figure/{id}` is **public** (not behind `X-API-Key`). Browser `<img>` tags can't send custom headers, so security relies on the 128-bit UUID4 figure_id being unguessable.

### DOCX export (Times New Roman, shared across all five modes)
- **What:** A single markdown→DOCX walker handles the assembled output of every pipeline. Headings map to Word styles (Heading 0/1/2), the body uses Times New Roman 12pt, headings 14/13/12pt.
- **For Thesis only:** When it encounters a `![Figure N](/api/thesis/figure/<id>)` markdown line, it resolves the ID through `figure_store.path_for()` and calls `doc.add_picture(path, width=Inches(5.5))`. Missing files fall back to a `[Figure unavailable: ...]` placeholder rather than crashing the export.
- **Where:** [`services/docx_export.py`](backend/app/services/docx_export.py). Wired through `POST /api/paper/export/docx`, which the frontend's `ExportButtons` calls for every pipeline.

### Server-sent events
- **What:** Both pipelines yield typed events (`started`, `section_completed`, `completed`, `error`, …). The API wraps them in SSE.
- **Why:** Users see live progress, not a spinner for 60 seconds.
- **Where:** API routes use `EventSourceResponse` from `sse-starlette`. Frontend parses with a custom fetch-based SSE reader in [`frontend/lib/sse.ts`](frontend/lib/sse.ts) (since `EventSource` can't POST).

---

## 8. MCP server

### What MCP is
The **Model Context Protocol** is an open standard for connecting LLMs to external tools and data. A server exposes tools; any MCP-compatible client (Claude Desktop, Claude Code, PydanticAI agents) can discover and call them.

### CorpusAI's MCP server
- **What:** A separate process that exposes the paper services as MCP tools over HTTP.
- **Why:** Lets your own agents (or external clients) query the paper index without going through the FastAPI HTTP layer. Future agents can chain external MCP servers (web search, Zotero) for free.
- **Where:** [`backend/app/mcp_server.py`](backend/app/mcp_server.py).
- **Tools exposed:**
  - `search_external_papers(query, limit)` — Semantic Scholar search
  - `list_ref_sets(user_id)` — enumerate sets
  - `get_ref_set(set_id, user_id)` — fetch metadata
  - `search_chunks(set_id, query, k, user_id)` — BM25 search inside a set
- **Run with:** `uv run python -m app.mcp_server` → `http://localhost:8765/mcp`

### MCP-server authentication
- **What:** A Starlette middleware in front of FastMCP rejects requests without a valid `X-API-Key` (when `APP_API_KEY` is set). Same convention as the FastAPI layer — share one secret, gate both endpoints.
- **Why:** The MCP server was previously open to anyone who could reach the port. Now it has the same gate as the REST API.
- **Where:** [`mcp_server.py:APIKeyMiddleware`](backend/app/mcp_server.py). Returns a 401 with `application/problem+json`.

---

## 9. Frontend

### Next.js 14 App Router
- Pages: `app/page.tsx` (the only route) wraps `ModeTabs`, which switches between five views: `ExploreView`, `WriteView`, `NHMRCView`, `ARCView`, and `ThesisView`. Each lives under `components/<mode>/`.
- The Thesis view has the most complex UI: dynamic chapter rows (add/remove), per-chapter PDF uploader, per-chapter figure picker with caption editor.

### Settings dialog
- **What:** Modal where users paste their API key and (optionally) a User ID. Stored in `localStorage`.
- **Why:** Bundling the API key into the JS at build time means every visitor sees it. A user-entered key is at least one degree of friction.
- **Where:** [`frontend/components/SettingsDialog.tsx`](frontend/components/SettingsDialog.tsx) + [`lib/auth.ts`](frontend/lib/auth.ts).
- **Reality check:** `NEXT_PUBLIC_API_KEY` (env-bundled) is still the fallback, so this isn't strong security — just a way to share one deployment across users without recompiling.

### SSE streaming view
- **What:** `StreamLog` shows each event as it arrives.
- **Where:** `frontend/components/ui/StreamLog.tsx` + `lib/sse.ts`.

### Auth-error surfacing (401/429)
- **What:** Both `streamSse` and the REST helpers in `api.ts` detect `401` and `429` responses and throw typed errors (`AuthRequiredError`, `RateLimitError`). The UI can catch these and re-open the Settings dialog or show a "wait a minute" toast.
- **Why:** Wrong API keys used to surface as a generic "stream failed (401)" message. Users had no idea they needed to open Settings.
- **Where:** [`frontend/lib/sse.ts`](frontend/lib/sse.ts) + [`frontend/lib/api.ts`](frontend/lib/api.ts).

---

## 10. CI / quality

### GitHub Actions
- **What:** Two jobs run on every push and PR — backend (`pytest` + `ruff check`) and frontend (`tsc --noEmit` + `npm run lint`).
- **Why:** Caught regressions during the PydanticAI migration. Cheap insurance.
- **Where:** [`.github/workflows/ci.yml`](.github/workflows/ci.yml).

### Test suite (48 tests)
- **Agents:** mocked `BaseAgent.run`, verifies render + parse
- **Workflows:** mocked LLM, exercises full event sequence (including the new `usage` event). Coverage includes Explore, Write, NHMRC, ARC, and Thesis workflows; thesis tests also assert figure marker rewriting and auto-titles.
- **Services:** real BM25 + real SQLite (using `tmp_path`); covers user-scoping + persistence across reopen
- **API:** real `TestClient`, real handlers, mocked LLM via fixture. Now also covers:
  - `verify_api_key` (401 on missing/wrong key, public `/health`)
  - RFC 7807 problem+json shape
  - `X-Request-ID` echo
  - `DELETE /api/paper/refs/{set_id}` (success, 404 on second delete, owner check)
- **Where:** `backend/tests/`. `conftest.py` redirects `DATA_DIR` to a temp dir so tests don't pollute the repo.

---

## 11. Deployment (Fly.io + Vercel)

### Why this stack
- **Fly.io** for the backend: cheapest provider that gives you an always-on machine with persistent volumes and SSE-friendly HTTP/2. ~$5/mo for a shared CPU + 1 GB RAM + 1 GB volume.
- **Vercel** for the frontend: free for Next.js, zero configuration, automatic preview deploys.
- **Total:** ~$5/month at this scale.

### One-time setup

```bash
# Install Fly CLI (Windows)
iwr https://fly.io/install.ps1 -useb | iex
fly auth signup

# Install Vercel CLI
npm i -g vercel
vercel login
```

### Deploy the backend

```bash
cd backend

# Edit fly.toml: change `app = "corpusai-backend"` to a unique name and
# pick a region close to you (syd, iad, fra, nrt).

fly launch --no-deploy --copy-config --name <your-app-name>

# Create the persistent volume for the SQLite store
fly volumes create corpusai_data --size 1 --region <your-region>

# Set secrets (never commit these)
fly secrets set \
  ANTHROPIC_API_KEY=sk-ant-... \
  APP_API_KEY=$(python -c "import secrets; print(secrets.token_urlsafe(32))") \
  CORS_ALLOWED_ORIGINS=https://<your-vercel-domain>.vercel.app \
  RATE_LIMIT_PER_MINUTE=10 \
  ENVIRONMENT=production

fly deploy
fly status
curl https://<your-app-name>.fly.dev/health   # → {"status": "ok"}
```

### Deploy the frontend

1. Push the repo to GitHub.
2. Go to <https://vercel.com/new>, import the repo.
3. Set **Root Directory** to `frontend`.
4. Add env vars:
   - `NEXT_PUBLIC_API_URL` = `https://<your-app-name>.fly.dev`
   - `NEXT_PUBLIC_API_KEY` = (same value you set as `APP_API_KEY` on Fly)
5. Deploy.

### What runs where

```
   ┌────────────────┐     ┌──────────────────────┐     ┌──────────────────┐
   │ Vercel (free)  │────▶│ Fly.io machine       │────▶│ Anthropic API    │
   │ Next.js bundle │     │ FastAPI + agents     │     │ (Claude Sonnet)  │
   └────────────────┘     └──────────────────────┘     └──────────────────┘
                                     │
                                     ▼
                          ┌──────────────────────┐
                          │ Fly volume (/data)   │
                          │ SQLite + uploaded    │
                          │ PDFs metadata        │
                          └──────────────────────┘
```

### Files involved
- [`backend/Dockerfile`](backend/Dockerfile) — production image
- [`backend/fly.toml`](backend/fly.toml) — Fly config (volume mount, health check, machine size)
- [`backend/.env.example`](backend/.env.example) — list of all backend env vars
- [`frontend/vercel.json`](frontend/vercel.json) — Vercel config
- [`frontend/.env.local.example`](frontend/.env.local.example) — list of all frontend env vars
- [`DEPLOY.md`](DEPLOY.md) — the same steps in a more terse, command-only format

---

## 12. Cheat sheet — env vars

### Backend (`backend/.env`)

| Var | Default | Purpose |
|---|---|---|
| `ANTHROPIC_API_KEY` | — | Required. Your Claude API key. |
| `ANTHROPIC_CHAT_MODEL` | `claude-sonnet-4-6` | Model used by every agent. |
| `APP_API_KEY` | "" | Shared key for `X-API-Key`. Empty = dev mode (auth bypassed). |
| `CORS_ALLOWED_ORIGINS` | `http://localhost:3000` | Comma-separated allowed origins. |
| `RATE_LIMIT_PER_MINUTE` | 10 | Per-IP cap on `/api/*` requests. |
| `ENVIRONMENT` | `development` | `production` switches logging to JSON. |
| `MAX_TOKENS_PER_REQUEST` | 2,000,000 | Workflow aborts if exceeded. |
| `RESULT_CACHE_SIZE` | 64 | Recent results held in memory. |
| `ENABLE_PROMPT_CACHE` | true | Anthropic system-prompt caching. |
| `DATA_DIR` | `./data` | Where the SQLite file lives. Use `/data` on Fly. |
| `LOG_LEVEL` | `INFO` | Standard log level. |

### Frontend (`frontend/.env.local`)

| Var | Default | Purpose |
|---|---|---|
| `NEXT_PUBLIC_API_URL` | `http://localhost:8000` | Backend base URL. |
| `NEXT_PUBLIC_API_KEY` | "" | Build-time fallback for `X-API-Key`. |

---

## Real gaps if strangers use it

Everything below is **not yet built**. Read this if you plan to expose CorpusAI to people you don't personally know.

### Auth is not real auth
- **Problem:** `X-API-Key` is a single shared secret. `X-User-ID` is trusted as-is — anyone can set it to anything and read another user's papers (if they know the user-id string).
- **What's needed:** Sign-in flow (Clerk, Auth0, NextAuth, or your own JWT). The user_id then comes from a verified token, not a header.

### No backups
- **Problem:** The SQLite file lives on a single Fly volume. Volume corruption or accidental deletion = total data loss.
- **What's needed:** `litestream` replication to S3, or `fly volumes snapshot` on a schedule.

### No error monitoring
- **Problem:** Errors go to stdout logs. Nobody gets paged when a deploy breaks or costs spike.
- **What's needed:** Sentry or similar — both backend (FastAPI) and frontend (Next.js) have first-class SDKs.

### No graceful degradation (frontend banner)
- **Problem:** Backend retries Anthropic failures (good), but if all retries exhaust, the user still sees a raw error event. There is no "Anthropic is down, please retry in 5 min" banner.
- **What's needed:** Inspect the final `error` event in the frontend and render a polite banner. Backend already gives you the typed error name.

### Per-user monthly spend cap
- **Problem:** Per-request cap exists (`MAX_TOKENS_PER_REQUEST`), but a single user can run 100 requests in a day. No monthly ceiling.
- **What's needed:** A `usage_log` SQLite table; check the user's running total at workflow start and refuse if over the monthly limit.

### Documentation gaps
- No "how does a non-technical user get started" guide.
- No description of what the 26 agents actually do (each has a prompt file — but no overview).

### Storage doesn't scale horizontally
- **Problem:** SQLite is local to the Fly volume. Running 2+ machines means 2+ disjoint databases.
- **What's needed:** Postgres (Fly has managed PG) or LiteFS-replicated SQLite when you outgrow one machine.

### PDF extraction is basic
- `pypdf` misses tables, math, and multi-column layouts. For real scientific papers, swap to `marker` or `unstructured` (heavier deps, sometimes need a GPU).

---

## What to read next

- **[CLAUDE.md](CLAUDE.md)** — the conventions every contributor follows.
- **[DEPLOY.md](DEPLOY.md)** — terse command-by-command deployment.
- Source code, in roughly this order if you're learning:
  1. [`backend/app/agents/base.py`](backend/app/agents/base.py) — the agent contract
  2. [`backend/app/workflows/explore.py`](backend/app/workflows/explore.py) — see how agents chain
  3. [`backend/app/services/reference_store.py`](backend/app/services/reference_store.py) — the storage layer
  4. [`backend/app/main.py`](backend/app/main.py) — middleware stack
