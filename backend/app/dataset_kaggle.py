"""
Kaggle datasets via `kagglehub` (optional dependency).

Default: **mohamedramadan2040/jobsphere-ats-resume-scoring** — résumé templates (commonly
`.docx`; `.pdf` under the same tree is picked up too). Text uses the same `extract_resume_text`
path as uploads.

Requires Kaggle API credentials for download (typical env):
  KAGGLE_USERNAME
  KAGGLE_KEY

Cache directory defaults to `backend/data/kagglehub_cache` (`KAGGLEHUB_CACHE`).
"""

from __future__ import annotations

import os
from collections.abc import Iterator
from pathlib import Path

DEFAULT_JOBSPHERE_SLUG = "mohamedramadan2040/jobsphere-ats-resume-scoring"


def resolve_jobsphere_slug(slug: str | None) -> str:
    return (slug or os.environ.get("KAGGLE_JOBSPHERE_DATASET") or DEFAULT_JOBSPHERE_SLUG).strip()


def ensure_kagglehub_cache() -> None:
    from app.paths import DATA_DIR

    cache = DATA_DIR / "kagglehub_cache"
    cache.mkdir(parents=True, exist_ok=True)
    os.environ.setdefault("KAGGLEHUB_CACHE", str(cache))


def download_kaggle_dataset(slug: str | None = None) -> Path:
    """Download (or use cached) dataset; returns root directory path."""
    ensure_kagglehub_cache()
    import kagglehub

    rid = resolve_jobsphere_slug(slug)
    return Path(kagglehub.dataset_download(rid))


def iter_kaggle_docx_resume_texts(
    root: Path,
    *,
    limit: int | None = None,
) -> Iterator[tuple[str, str]]:
    """
    Walk `root` for `.docx` and `.pdf` files; yield (filename, extracted_text).
    Skips files that fail to parse or yield very little text.
    """
    from app.parsers import extract_resume_text

    globs: list[list[Path]] = [sorted(root.rglob("*.docx")), sorted(root.rglob("*.pdf"))]
    files = sorted({p.resolve() for group in globs for p in group}, key=lambda p: str(p).lower())

    n = 0
    for fp in files:
        if limit is not None and n >= limit:
            break
        try:
            data = fp.read_bytes()
            text = extract_resume_text(fp.name, data)
        except Exception:
            continue
        text = text.strip()
        if len(text) < 50:
            continue
        yield fp.name, text
        n += 1
