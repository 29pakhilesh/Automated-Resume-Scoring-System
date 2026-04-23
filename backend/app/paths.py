"""Repository layout: backend package, repo root, frontend build output, persisted data."""

from pathlib import Path

# backend/app/paths.py → backend/
BACKEND_ROOT = Path(__file__).resolve().parent.parent
# Monorepo root (parent of backend/)
REPO_ROOT = BACKEND_ROOT.parent

DATA_DIR = BACKEND_ROOT / "data"
FRONTEND_DIST = REPO_ROOT / "frontend" / "dist"
ENV_FILE = REPO_ROOT / ".env"
