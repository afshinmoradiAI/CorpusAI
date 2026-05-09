# Deploying CorpusAI

Backend runs on **Fly.io** (single always-on machine, SSE-friendly).
Frontend runs on **Vercel** (free tier).

---

## Prereqs (one-time)

```bash
# Fly CLI
# Windows (PowerShell):
iwr https://fly.io/install.ps1 -useb | iex
# macOS / Linux:
curl -L https://fly.io/install.sh | sh

fly auth signup        # or `fly auth login` if you already have an account

# Vercel CLI (optional — you can also deploy via the dashboard)
npm i -g vercel
vercel login
```

---

## 1. Deploy the backend

```bash
cd backend

# Edit fly.toml: change `app = "corpusai-backend"` to a globally unique name.
# Pick a region close to you (syd, iad, fra, nrt, etc).

fly launch --no-deploy --copy-config --name <your-app-name>
# This registers the app on Fly without launching yet.

fly secrets set \
  ANTHROPIC_API_KEY=sk-ant-... \
  CORS_ALLOWED_ORIGINS=http://localhost:3000

fly deploy

# Verify
fly status
curl https://<your-app-name>.fly.dev/health
# → {"status":"ok","model":"claude-sonnet-4-6","api_key_configured":"yes"}
```

If the build fails on dependency resolution, run `uv lock` locally and commit the
refreshed `uv.lock` before retrying.

---

## 2. Deploy the frontend

The frontend is a stock Next.js 14 app. Vercel auto-detects everything.

**Via the dashboard (recommended for first time):**

1. Go to https://vercel.com/new and import the GitHub repo.
2. Set **Root Directory** to `frontend`.
3. Add env var **`NEXT_PUBLIC_API_URL`** = `https://<your-app-name>.fly.dev`.
4. Click **Deploy**.

**Via CLI:**

```bash
cd frontend
vercel --prod
# Answer prompts; set NEXT_PUBLIC_API_URL when asked, or:
vercel env add NEXT_PUBLIC_API_URL production
# (paste https://<your-app-name>.fly.dev)
vercel --prod
```

---

## 3. Wire CORS to the production frontend

Once Vercel gives you a URL (e.g. `https://corpusai-frontend.vercel.app`):

```bash
cd backend
fly secrets set \
  CORS_ALLOWED_ORIGINS="https://corpusai-frontend.vercel.app,http://localhost:3000"
# Setting secrets restarts the machine automatically.
```

You're done.

---

## Operating notes

- **Single instance only.** The in-memory `ReferenceStore` (uploaded PDFs +
  BM25 index) is per-process. Do **not** raise `min_machines_running` above 1
  or scale to multiple regions until you swap the store for Postgres + S3.
- **Restarts wipe state.** Users will lose their uploaded PDFs across deploys
  and machine restarts. Acceptable for an MVP — re-upload is fast.
- **Costs.** Fly machine: ~$2/mo when idle, more under load. Anthropic API
  dominates: ~$0.10–0.30 per Write run on Sonnet 4.6.
- **Logs:** `fly logs`. Enter the running container with `fly ssh console`.
- **Rollback:** `fly releases` then `fly deploy --image <previous-image>`.

---

## When to outgrow this setup

Move the `ReferenceStore` out of memory the moment any of these become true:

- More than one human uses the app concurrently.
- You need uploads to survive deploys.
- You need to run more than one backend machine for redundancy.

Smallest practical replacement: Fly Postgres for `RefSet` + `Chunk`, Fly
Volumes (or S3) for the raw PDF bytes, BM25 rebuilt on machine start.
