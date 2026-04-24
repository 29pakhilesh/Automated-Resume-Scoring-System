"""Runtime configuration (env vars)."""

import os
from dataclasses import dataclass

from app.paths import DATA_DIR


def _env(name: str, default: str | None = None) -> str | None:
    v = os.environ.get(name)
    return v if v is not None and v != "" else default


def _default_sqlite_url() -> str:
    path = DATA_DIR / "rss.db"
    return f"sqlite+aiosqlite:///{path.as_posix()}"


@dataclass(frozen=True)
class Settings:
    database_url: str
    embedding_model: str
    llm_max_tokens: int
    scoring_weight_format: float
    scoring_weight_semantic: float
    scoring_weight_keywords: float
    # Scoring run persistence (see app/scoring_privacy.py)
    persist_scoring_runs: bool
    store_scoring_sensitive_content_in_db: bool


def _truthy(name: str, default: str = "false") -> bool:
    v = (_env(name, default) or default).strip().lower()
    return v in {"1", "true", "yes", "on"}


def get_settings() -> Settings:
    return Settings(
        database_url=_env("DATABASE_URL") or _default_sqlite_url(),
        embedding_model=_env(
            "EMBEDDING_MODEL",
            "all-MiniLM-L6-v2",
        )
        or "all-MiniLM-L6-v2",
        llm_max_tokens=int(_env("LLM_MAX_TOKENS", "700") or "700"),
        scoring_weight_format=float(_env("SCORING_WEIGHT_FORMAT", "0.18") or "0.18"),
        scoring_weight_semantic=float(_env("SCORING_WEIGHT_SEMANTIC", "0.50") or "0.50"),
        scoring_weight_keywords=float(_env("SCORING_WEIGHT_KEYWORDS", "0.32") or "0.32"),
        # Off by default: no scoring history in DB until explicitly enabled (e.g. local analytics).
        persist_scoring_runs=_truthy("PERSIST_SCORING_RUNS", "false"),
        # When false (default): no JD excerpt, filenames, or full payload blobs in DB—safe for deploy.
        store_scoring_sensitive_content_in_db=_truthy("STORE_SCORING_SENSITIVE_CONTENT_IN_DB", "false"),
    )
