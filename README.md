# Resume Scoring System

Score a resume against a specific job description. The app returns an overall score, subscores, and a details page that shows what’s driving the result.

## Tech stack

![FastAPI](https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=white)
![Python](https://img.shields.io/badge/Python-3776AB?logo=python&logoColor=white)
![Uvicorn](https://img.shields.io/badge/Uvicorn-111827?logo=python&logoColor=white)
![React](https://img.shields.io/badge/React-61DAFB?logo=react&logoColor=0B1020)
![TypeScript](https://img.shields.io/badge/TypeScript-3178C6?logo=typescript&logoColor=white)
![Vite](https://img.shields.io/badge/Vite-646CFF?logo=vite&logoColor=white)
![TailwindCSS](https://img.shields.io/badge/Tailwind_CSS-06B6D4?logo=tailwindcss&logoColor=white)
![Framer Motion](https://img.shields.io/badge/Framer_Motion-0055FF?logo=framer&logoColor=white)
![Lucide](https://img.shields.io/badge/Lucide-111827?logo=lucide&logoColor=white)
![SQLite](https://img.shields.io/badge/SQLite-003B57?logo=sqlite&logoColor=white)

## Features

- **Overall score + subscores**: format/structure, semantic fit, keyword fit.
- **Details page**: shows weak sections (text) and the main metrics behind the score.
- **OCR fallback**: tries OCR for scanned/image-heavy PDFs (requires system `tesseract`).
- **Monorepo**: `backend/` (FastAPI) + `frontend/` (React/Vite).

## Project structure

```text
RSS/
  backend/                 FastAPI app (run from this cwd)
    app/
    requirements.txt
    data/                  SQLite + caches (ignored)
  frontend/                React + Vite source
    src/
    dist/                  Production build output (served by backend when present)
  Makefile
  .env                     Optional runtime config (repo root)
```

## Quickstart

### Prerequisites

- **Python 3.10+**
- **Node.js 18+**
- (Optional) **Tesseract OCR** for scanned PDFs / image resumes:
  - macOS: `brew install tesseract`

### Install

```bash
make install-all
```

### Run (single command)

```bash
make dev
```

This starts the API at `http://127.0.0.1:8000` and opens the app in your browser once it’s ready.

### Run with UI hot reload (recommended for frontend work)

Terminal A:

```bash
make dev-api
```

Terminal B:

```bash
make dev-ui
```

Vite runs on `http://127.0.0.1:5173` and proxies `/api` to the backend.

## Configuration (`.env`)

Create a repo-root `.env` if you want to change defaults.

### Scoring weights

The overall score is a weighted blend of the three subscores:

\[
\text{overall}=\frac{w_f\cdot \text{format}+w_s\cdot \text{semantic}+w_k\cdot \text{keywords}}{w_f+w_s+w_k}
\]

```env
SCORING_WEIGHT_FORMAT=0.18
SCORING_WEIGHT_SEMANTIC=0.50
SCORING_WEIGHT_KEYWORDS=0.32
```

You can verify the currently loaded weights at:

- `GET /api/health`

### Persistence (optional)

By default, scoring runs are **not** persisted. If you enable persistence, the app is conservative about storing sensitive content:

```env
PERSIST_SCORING_RUNS=false
STORE_SCORING_SENSITIVE_CONTENT_IN_DB=false
```

## API

- `POST /api/score`: main scoring endpoint (multipart form: `file`, `position_title`, `job_description`)
- `GET /api/health`: health + currently loaded scoring weights
- `GET /api/runs`: recent runs (when persistence enabled)

## Troubleshooting

- **“Very little text extracted”**:
  - Your PDF may be scanned/image-only.
  - Install `tesseract` and retry, or use a text-based PDF/DOCX export.
- **No OCR available**:
  - OCR requires the system `tesseract` binary in PATH.
- **Frontend can’t reach backend**:
  - Use `make dev` (single-server) or `make dev-api` + `make dev-ui` (Vite proxy).

## Commands

```bash
make help
make install
make install-frontend
make install-all
make build
make dev
make dev-api
make dev-ui
```

