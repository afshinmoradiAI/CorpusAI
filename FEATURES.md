# Feature checklist (reusable across projects)

Every feature considered for CorpusAI, flat list, grouped by concern. Use this as a checklist when building a new app: scan top-to-bottom, decide which apply, and pull the relevant code/config from this repo.

Legend: ✅ shipped · ⚠️ partial · ❌ deferred

---

## 1. Agent framework
- ✅ Type-safe agent framework (PydanticAI)
- ✅ Pydantic models for every agent input/output
- ✅ Base class with `prompt_name` + `output_model` + `render_input()` contract
- ✅ Prompts on disk (`prompts/*.md`), not hardcoded in Python
- ✅ Lazy agent construction (cheap to instantiate, expensive on first call)
- ✅ Per-agent model override (mix Sonnet + Haiku)
- ✅ Workflow orchestrator (agents never call each other directly)
- ✅ Async-everywhere

## 2. Authentication & access control
- ✅ Shared API-key auth (`X-API-Key` header)
- ✅ Per-user scoping via `X-User-ID` header
- ✅ Dev-mode bypass when no key configured
- ❌ Real auth (JWT / OAuth / Clerk / NextAuth)
- ❌ Role-based access control
- ❌ API-key rotation strategy

## 3. Rate limiting & abuse protection
- ✅ Per-IP rate limit (`slowapi`, default 10/min)
- ✅ Pydantic input length caps (min/max)
- ✅ File upload limits (count, size, MIME)
- ✅ Scrubbed health endpoint (no leak of model/version)
- ❌ Per-user monthly quota
- ❌ Captcha for anonymous uploads

## 4. Errors & observability
- ✅ RFC 7807 problem+json responses
- ✅ Structured logging (`structlog`, JSON in prod, console in dev)
- ✅ Request-ID middleware (accept or generate, echo back)
- ✅ Per-agent token-usage logging
- ✅ Retry on transient failures (`tenacity`, exp backoff + jitter, 429/5xx only)
- ❌ Error monitoring (Sentry / Honeybadger / Rollbar)
- ❌ Distributed tracing (OpenTelemetry / Logfire)
- ❌ Frontend graceful-degradation banner

## 5. Persistence & storage
- ✅ SQLite with WAL + foreign keys + cascade delete
- ✅ Schema: `parents` ← `documents` ← `chunks`
- ✅ User-scoped rows (`user_id` nullable for anonymous)
- ✅ Configurable data dir (`DATA_DIR`)
- ✅ Persistent volume on Fly.io
- ✅ Data deletion endpoint (`DELETE /resource/{id}`)
- ❌ Automated backups (litestream → S3/R2)
- ❌ Horizontal scaling (Postgres / LiteFS)

## 6. Search / retrieval
- ✅ BM25 over text chunks (`rank-bm25`)
- ✅ Lazy index build, in-process LRU cache
- ❌ Embeddings / vector DB
- ❌ Hybrid retrieval (BM25 + vectors)
- ❌ Re-ranker pass

## 7. Caching
- ✅ Anthropic prompt caching (`anthropic_cache_instructions`)
- ✅ Workflow result cache (in-memory LRU, SHA-256 keys)
- ❌ Redis / distributed cache
- ❌ HTTP response cache (CDN)

## 8. Cost control
- ✅ Per-request spend cap (contextvars budget)
- ✅ Token-usage logging at workflow completion
- ✅ Cost-visibility SSE event (`{tokens, est_cost_usd, breakdown}`)
- ✅ Mixed-model strategy (Haiku for mechanical agents, Sonnet for reasoning)
- ❌ Per-user monthly cap
- ❌ Pre-flight cost estimate before running
- ❌ Stripe usage metering

## 9. Workflows & streaming
- ✅ Async generator orchestrators
- ✅ Typed event enums (`Literal["started", "completed", ...]`)
- ✅ Server-sent events (`sse-starlette`)
- ✅ Parallel agent execution (`asyncio.gather`)
- ✅ Skip-on-fail (workflow continues if one parallel agent dies)
- ❌ Token-level streaming (PydanticAI `run_stream`)
- ❌ Workflow resume from checkpoint
- ❌ Background job queue (Celery / Arq) for very long runs

## 10. API design
- ✅ FastAPI + Pydantic
- ✅ All routes async
- ✅ Dependency injection (`Depends(...)`)
- ✅ Auto-generated `/docs` + `/openapi.json`
- ✅ Versioned schemas (`schemas/*.py`)
- ✅ Standard CRUD verbs (POST upload, GET list, DELETE remove)
- ✅ SSE for long-running operations
- ❌ GraphQL
- ❌ gRPC

## 11. MCP integration
- ✅ MCP server exposing services as tools
- ✅ Streamable HTTP transport
- ✅ API-key middleware on MCP server
- ❌ MCP client (consuming external MCP servers from agents)
- ❌ MCP server registry / discovery

## 12. Frontend
- ✅ Next.js 14 App Router
- ✅ TypeScript strict
- ✅ Tailwind
- ✅ Custom SSE client (fetch-based, supports POST)
- ✅ Settings dialog with `localStorage` for API key + user_id
- ✅ Typed error classes (`AuthRequiredError`, `RateLimitError`)
- ✅ Auth-header helper used by every request
- ❌ Service-unavailable banner
- ❌ Auth dialog auto-open on 401
- ❌ Loading skeletons / optimistic UI
- ❌ Accessibility audit (Lighthouse / axe)
- ❌ i18n

## 13. Testing
- ✅ pytest with `asyncio_mode = auto`
- ✅ Mocked LLM calls (monkey-patched `BaseAgent.run`)
- ✅ Workflow end-to-end tests (full event sequence)
- ✅ Service tests with real SQLite + `tmp_path`
- ✅ API tests with `TestClient`
- ✅ Auth + 401 + 422 + RFC 7807 shape tests
- ✅ Test fixtures isolate `DATA_DIR` per session
- ❌ Frontend unit tests (Vitest / Jest)
- ❌ End-to-end browser tests (Playwright)
- ❌ Property-based tests (Hypothesis)
- ❌ Load tests (Locust / k6)

## 14. CI / quality
- ✅ GitHub Actions on push + PR
- ✅ Backend: pytest + ruff
- ✅ Frontend: tsc + lint
- ❌ Auto-format on PR
- ❌ Coverage reporting
- ❌ Auto-deploy on merge to main
- ❌ Dependency vulnerability scanning (Dependabot / Snyk)
- ❌ Secret scanning (gitleaks)

## 15. Configuration
- ✅ `pydantic-settings` with env-var aliases
- ✅ `.env` file support
- ✅ `.env.example` with every var documented
- ✅ `lru_cache` singleton for settings
- ✅ Environment switch (`ENVIRONMENT=development|production`)

## 16. Containerisation & deployment
- ✅ Dockerfile (multi-stage, slim base image)
- ✅ `.dockerignore` to keep image small
- ✅ Fly.io config (`fly.toml`) with volume mount + healthcheck
- ✅ Vercel config (`vercel.json`) for frontend
- ✅ Pre-flight checklist in README
- ✅ Deployment runbook (`DEPLOY.md`)
- ✅ Target cost ~$5/month
- ❌ Blue/green deploys
- ❌ Multi-region deploy

## 17. Documentation
- ✅ `README.md` — overview + quick start + pre-flight
- ✅ `TUTORIAL.md` — every feature, grouped by category, with code refs
- ✅ `DEPLOY.md` — terse command-by-command deploy
- ✅ `CLAUDE.md` — codebase conventions for contributors
- ✅ `FEATURES.md` — this file
- ✅ Honest "Real gaps" section listing what's NOT done
- ❌ Architecture decision records (ADRs)
- ❌ User-facing docs site
- ❌ Per-agent description / role summary

## 18. Repo hygiene
- ✅ Conventional repo layout (`backend/`, `frontend/`, top-level docs)
- ✅ `.gitignore` for `.env`, `data/`, `*.sqlite`, build artefacts
- ❌ `Makefile` / `task` runner
- ❌ Pre-commit hooks
- ❌ CHANGELOG.md
- ❌ License file

## 19. Privacy / compliance
- ✅ User-data deletion endpoint
- ✅ Per-user data isolation (header-based)
- ❌ Audit log of user actions
- ❌ Data export endpoint (GDPR Article 20)
- ❌ Privacy policy / Terms of service
- ❌ Cookie consent banner

## 20. Future considerations (commonly needed)
- Account creation + email verification
- Password reset flow
- Stripe / payments
- Webhook receiver
- Admin panel
- Feature flags (LaunchDarkly / Unleash / Statsig)
- A/B testing infra
- Email transactional (Resend / Postmark)
- Search analytics (which queries fail?)
- User feedback widget

---

## How to use this for a new app

1. **Copy this file** into the new repo as `FEATURES.md`.
2. **Reset every ✅ to ❌** — you're starting from zero.
3. **Mark the must-haves** before MVP, then check them off as you build.
4. **Cross-reference the code** in this CorpusAI repo for each pattern — most are 10–30 lines and copy-paste-ready.

## File map (where each feature lives in this repo)

| Concern | Files to copy |
|---|---|
| Agent base + retries + caching | `backend/app/agents/base.py` |
| Config | `backend/app/core/config.py` + `.env.example` |
| Auth dependency | `backend/app/core/security.py` |
| Logging | `backend/app/core/logging.py` |
| RFC 7807 | `backend/app/core/problem.py` |
| LRU cache | `backend/app/core/cache.py` |
| Spend cap | `backend/app/core/usage.py` |
| Persistent store | `backend/app/services/reference_store.py` |
| BM25 | `backend/app/services/retrieval.py` |
| Main + middleware | `backend/app/main.py` |
| Rate limit + auth on routes | `backend/app/api/routes_*.py` |
| MCP server | `backend/app/mcp_server.py` |
| CI | `.github/workflows/ci.yml` |
| Deploy | `backend/Dockerfile` + `backend/fly.toml` |
| Frontend auth + SSE | `frontend/lib/{auth,api,sse}.ts` |
| Settings dialog | `frontend/components/SettingsDialog.tsx` |
