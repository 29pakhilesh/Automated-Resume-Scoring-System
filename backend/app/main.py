import os
from contextlib import asynccontextmanager
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.api.routes import router as api_router
from app.db.session import init_db
from app.paths import DATA_DIR, ENV_FILE, FRONTEND_DIST

load_dotenv(ENV_FILE)


@asynccontextmanager
async def lifespan(app: FastAPI):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    await init_db()
    yield


app = FastAPI(title="Resume Scoring System", version="0.4.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)


def _register_frontend(app: FastAPI, dist: Path) -> None:
    """Serve the Vite build without mounting StaticFiles at `/` (POST /api/* would get 405)."""
    dist = dist.resolve()
    index_path = dist / "index.html"
    if not index_path.is_file():
        return

    assets_dir = dist / "assets"
    if assets_dir.is_dir():
        app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="vite_assets")

    @app.get("/", include_in_schema=False)
    async def spa_index():
        return FileResponse(index_path)

    @app.get("/{full_path:path}", include_in_schema=False)
    async def spa_fallback(full_path: str):
        # Let API + OpenAPI routes handle their paths (this route is GET-only; POST never hits here).
        if (
            full_path.startswith("api/")
            or full_path.startswith("docs")
            or full_path.startswith("redoc")
            or full_path == "openapi.json"
        ):
            raise HTTPException(status_code=404)
        candidate = (dist / full_path).resolve()
        try:
            candidate.relative_to(dist)
        except ValueError:
            return FileResponse(index_path)
        if candidate.is_file():
            return FileResponse(candidate)
        return FileResponse(index_path)


if os.path.isdir(FRONTEND_DIST):
    _register_frontend(app, Path(FRONTEND_DIST))
