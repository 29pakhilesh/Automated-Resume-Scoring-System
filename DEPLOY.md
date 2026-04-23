# Deploy: Vercel (frontend) + Render (backend)

The UI is a static Vite build that talks to a separate FastAPI API. Point the UI at the API with `VITE_API_BASE` at **build** time.

## Prerequisites

- Commit `backend/data/jd_archetypes.jsonl` so sample job roles load in production (and ship in the Docker image).
- The API image includes PyTorch and `sentence-transformers`; use a Render instance with **enough RAM** (starter or higher is safer than the smallest free tier for first cold start).

## 1. Render (API)

1. Push this repo to GitHub (or GitLab/Bitbucket).
2. In [Render](https://render.com): **New** → **Blueprint** → connect the repo → Render reads `render.yaml`.
   - Or **New** → **Web Service** → connect repo → set:
     - **Runtime**: Docker
     - **Dockerfile path**: `backend/Dockerfile`
     - **Docker build context**: `backend`
3. Wait for the first deploy (Docker build can take several minutes).
4. Copy the service URL, e.g. `https://rss-backend-xxxx.onrender.com` (no trailing slash).

Optional environment variables (Render → Environment):

| Variable | Purpose |
|----------|---------|
| `OPENAI_API_KEY` | Enables remote coach when `ENABLE_OPENAI_COACH=true` |
| `ENABLE_OPENAI_COACH` | `true` / `false` |
| `PERSIST_SCORING_RUNS` | `true` to store run history in SQLite on disk |
| `DATABASE_URL` | Override SQLite (e.g. managed Postgres URL) |

Free web services **spin down** after idle; the first request after sleep can take a minute while the container wakes.

## 2. Vercel (UI)

1. [Vercel](https://vercel.com) → **Add New** → **Project** → import the same repo.
2. **Root Directory**: `frontend`
3. **Framework Preset**: Vite (auto-detected).
4. **Environment Variables** (Production — required for the UI to reach Render):

   | Name | Value |
   |------|--------|
   | `VITE_API_BASE` | `https://rss-backend-xxxx.onrender.com` (your Render URL, no `/` at the end) |

5. Deploy. Open the Vercel URL; scoring calls go to Render.

`frontend/vercel.json` adds SPA rewrites so `/details` and reloads work.

## 3. Smoke test

- `GET https://<render-host>/api/health` → `{"status":"ok",...}`
- In the Vercel app: load archetypes, run a score on a small PDF/DOCX.

## Local Docker (optional)

```bash
docker build -f backend/Dockerfile -t rss-api backend
docker run --rm -p 8000:8000 -e PORT=8000 rss-api
```

Then `http://localhost:8000/api/health` and, with `VITE_API_BASE=http://localhost:8000`, `npm run dev` in `frontend/`.
