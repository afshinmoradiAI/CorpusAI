# CorpusAI — Deployment Guide

A single guide covering local dev plus every deployment option, ranked from
easiest to most complex. Pick one; you don't need them all.

---

## What you're deploying

Two services:

| Service | Stack | Port | Image |
|---------|-------|------|-------|
| **Backend** | FastAPI + Python 3.11 + uv | 8000 | `backend/Dockerfile` |
| **Frontend** | Next.js 16 (standalone) | 3000 | `frontend/Dockerfile` |

Both are stateless except for the SQLite reference store and uploaded figures.
For production at scale you'd swap SQLite for Postgres and the figure dir for
S3/GCS, but for personal / lab use the defaults are fine.

### Required secrets

| Name | Where it's used | How to get it |
|------|-----------------|---------------|
| `ANTHROPIC_API_KEY` | Backend | https://console.anthropic.com |
| `API_KEY` | Backend (auth) | Pick any random string |
| `NEXT_PUBLIC_API_URL` | Frontend build | Set to backend's public URL |
| `ALLOWED_ORIGINS` | Backend | Set to frontend's public URL |

---

## Option 0: Run locally

Two terminals.

```bash
# Terminal 1 — backend
cd backend
uv sync
uv run uvicorn app.main:app --reload
# → http://localhost:8000

# Terminal 2 — frontend
cd frontend
npm install
npm run dev
# → http://localhost:3000
```

Create `backend/.env` with `ANTHROPIC_API_KEY=sk-ant-...` first.

---

## Option 1: Fly.io (easiest, single command)

Best for solo / lab use. ~$5/month for both services.

```bash
# Install once
iwr https://fly.io/install.ps1 -useb | iex      # Windows
curl -L https://fly.io/install.sh | sh          # Mac/Linux

fly auth login

# Backend
cd backend
fly launch --no-deploy        # accept defaults; uses backend/Dockerfile
fly secrets set ANTHROPIC_API_KEY=sk-ant-... API_KEY=$(openssl rand -hex 16)
fly deploy

# Frontend
cd ../frontend
fly launch --no-deploy
fly secrets set NEXT_PUBLIC_API_URL=https://YOUR-BACKEND.fly.dev
fly deploy
```

That's it. Open the URL Fly prints.

---

## Option 2: Vercel (frontend only) + Fly.io (backend)

Vercel was built for Next.js — fastest frontend deploys, free tier.

```bash
cd frontend
npx vercel              # follow prompts, link to your GitHub repo
npx vercel env add NEXT_PUBLIC_API_URL production   # paste backend URL
npx vercel --prod
```

Deploy the backend on Fly.io as in Option 1.

---

## Option 3: Google Cloud Run (one-command full deploy)

Best free tier of the big-three clouds. Builds + deploys both services from
the included `cloudbuild.yaml`.

### One-time setup

```bash
gcloud config set project YOUR_PROJECT_ID

# Enable services
gcloud services enable cloudbuild.googleapis.com run.googleapis.com \
                       artifactregistry.googleapis.com secretmanager.googleapis.com

# Create an image registry
gcloud artifacts repositories create corpusai \
    --repository-format=docker --location=us-central1

# Store secrets
echo -n "sk-ant-..." | gcloud secrets create anthropic-api-key --data-file=-
echo -n "$(openssl rand -hex 16)" | gcloud secrets create api-key --data-file=-

# Let Cloud Run read those secrets
PROJECT_NUMBER=$(gcloud projects describe YOUR_PROJECT_ID --format='value(projectNumber)')
for secret in anthropic-api-key api-key; do
  gcloud secrets add-iam-policy-binding $secret \
    --member="serviceAccount:${PROJECT_NUMBER}-compute@developer.gserviceaccount.com" \
    --role="roles/secretmanager.secretAccessor"
done
```

### Every deploy

```bash
gcloud builds submit --config=cloudbuild.yaml
```

That builds both Docker images, pushes them, deploys backend, captures its
URL, builds frontend with that URL baked in, and deploys frontend. ~5 min.

---

## Option 4: AWS App Runner

The two `apprunner.yaml` files (`backend/apprunner.yaml` and
`frontend/apprunner.yaml`) make this a UI-click deploy.

### Backend

1. Push repo to GitHub.
2. AWS Console → **App Runner** → **Create service**
3. Source: **GitHub** → pick this repo, branch `main`
4. Deployment trigger: **Automatic**
5. Configuration: **Use a configuration file** → path `backend/apprunner.yaml`
6. Service name: `corpusai-backend`
7. Add environment variables:
   - `ANTHROPIC_API_KEY` = your key (set as secret)
   - `API_KEY` = random string
8. Create. Wait ~5 min. Copy the public URL.

### Frontend

Same flow, but:
- Path: `frontend/apprunner.yaml`
- Service name: `corpusai-frontend`
- Environment: `NEXT_PUBLIC_API_URL` = backend URL from above

---

## Option 5: Azure Container Apps

No config file needed.

```bash
az login
az group create --name corpusai --location eastus

# Backend
az containerapp up \
  --name corpusai-backend \
  --resource-group corpusai \
  --source backend \
  --ingress external --target-port 8000 \
  --env-vars ANTHROPIC_API_KEY=sk-ant-... API_KEY=$(openssl rand -hex 16)

# Note the FQDN it prints, then:
az containerapp up \
  --name corpusai-frontend \
  --resource-group corpusai \
  --source frontend \
  --ingress external --target-port 3000 \
  --env-vars NEXT_PUBLIC_API_URL=https://corpusai-backend.YOUR-REGION.azurecontainerapps.io
```

---

## Cost & scale comparison

| Option | Setup time | Free tier | Typical $/month (light use) | Best for |
|--------|-----------|-----------|-------------------------------|----------|
| Fly.io | 5 min | yes | $0–5 | Personal, demos |
| Vercel + Fly | 10 min | yes | $0–5 | Best Next.js performance |
| Cloud Run | 15 min | 2M req/mo | $0–10 | Bursty workloads, auto-scale to 0 |
| AWS App Runner | 10 min (clicks) | none | $25+ | Already on AWS |
| Azure CA | 10 min | 180k vCPU-s | $0–15 | Already on Azure |

---

## After deployment — checklist

- [ ] Open the frontend URL; verify the landing page loads
- [ ] Open `/explore` (Proposal); enter a topic; confirm SSE streaming works
- [ ] Open `/write` (Paper); upload a PDF; confirm chunks index successfully
- [ ] Check backend logs for "Anthropic API key not set" — common gotcha
- [ ] In browser DevTools → Network: confirm requests go to `NEXT_PUBLIC_API_URL`,
      not `localhost:8000`
- [ ] Set `ALLOWED_ORIGINS` on backend to your frontend URL (otherwise CORS
      will block in production)

---

## Troubleshooting

**"Failed to fetch" in browser** → `NEXT_PUBLIC_API_URL` was wrong at build
time. Rebuild the frontend image with the correct backend URL.

**CORS error** → Set `ALLOWED_ORIGINS=https://your-frontend-url` on the backend.

**Backend OOM during PDF upload** → bump memory to 1 GiB (Cloud Run/App Runner
default is 512 MiB). PyPDF text extraction is memory-hungry.

**Streaming hangs after ~30 s** → some clouds buffer SSE. Cloud Run, Fly.io,
and App Runner all stream correctly. Cloudflare in front of any of them does
*not* — disable proxy or use a non-Cloudflare CDN.

**Anthropic 429 / rate limit** → reduce `paper_limit` in `workflows/explore.py`
or upgrade your Anthropic tier.

---

## Recommended setup

For a researcher running CorpusAI personally:

> **Fly.io** for both services (~$5/mo, simplest) **or**
> **Vercel + Fly.io** if you want the slickest frontend.

For a lab / shared deployment:

> **Google Cloud Run** — auto-scales to zero when nobody is using it,
> generous free tier, one-command deploys via `cloudbuild.yaml`.
