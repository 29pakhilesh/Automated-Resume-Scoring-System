"""
Hugging Face datasets used for benchmarking (optional dependency: `datasets`).

The public resume–ATS corpus is published as **0xnbk/resume-ats-score-v1-en**
(note: leading **zero**, not the letter `o`). A common typo `oxnbk/...` is mapped
automatically.

Columns: `text` (resume), `ats_score` (float 0–100), `original_label` (e.g. Good Fit).
There is **no per-row job description**; benchmarks use a fixed generic JD so our
pipeline (which expects title + JD + resume) can still run and we can compare
correlation / MAE to `ats_score` as a sanity check—not a ground-truth match.
"""

from __future__ import annotations

import os
from typing import Any

# Correct Hub id (digit 0). User-supplied "oxnbk/..." is redirected here.
DEFAULT_RESUME_ATS_REPO = "0xnbk/resume-ats-score-v1-en"
_REPO_ALIASES: dict[str, str] = {
    "oxnbk/resume-ats-score-v1-en": DEFAULT_RESUME_ATS_REPO,
}


def resolve_resume_ats_repo_id(repo_id: str | None) -> str:
    rid = (repo_id or os.environ.get("HF_RESUME_ATS_DATASET") or DEFAULT_RESUME_ATS_REPO).strip()
    return _REPO_ALIASES.get(rid, rid)


def ensure_hf_datasets_cache() -> None:
    """Keep dataset cache inside the repo under backend/data (same pattern as HF models)."""
    from app.paths import DATA_DIR

    cache = DATA_DIR / "hf_datasets_cache"
    cache.mkdir(parents=True, exist_ok=True)
    os.environ.setdefault("HF_DATASETS_CACHE", str(cache))


def load_resume_ats_score_dict(repo_id: str | None = None) -> Any:
    """Load full DatasetDict (train + validation). Requires `pip install datasets`."""
    ensure_hf_datasets_cache()
    from datasets import load_dataset

    return load_dataset(resolve_resume_ats_repo_id(repo_id))


def load_resume_ats_split(
    repo_id: str | None = None,
    *,
    split: str = "validation",
    max_rows: int | None = None,
) -> Any:
    """Load one split; optionally truncate to the first `max_rows` examples."""
    ds = load_resume_ats_score_dict(repo_id)[split]
    if max_rows is not None and max_rows > 0:
        n = min(max_rows, len(ds))
        ds = ds.select(range(n))
    return ds
