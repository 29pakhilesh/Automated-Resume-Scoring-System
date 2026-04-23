"""Dense sentence embeddings for resume ↔ job-description similarity."""

from __future__ import annotations

import os
import threading
from typing import Any

import numpy as np

from app.paths import DATA_DIR

_HF_HOME = DATA_DIR / "hf_home"
_HF_HOME.mkdir(parents=True, exist_ok=True)
os.environ.setdefault("HF_HOME", str(_HF_HOME))
os.environ.setdefault("SENTENCE_TRANSFORMERS_HOME", str(_HF_HOME / "sentence_transformers"))

_lock = threading.Lock()
_model = None
_model_name: str | None = None


def _load_model(name: str) -> Any:
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer(name)


def get_embedding_model(model_name: str) -> Any:
    global _model, _model_name
    with _lock:
        if _model is None or _model_name != model_name:
            _model = _load_model(model_name)
            _model_name = model_name
        return _model


def embedding_similarity(
    resume_text: str,
    job_text: str,
    model_name: str,
    max_chars: int = 12000,
) -> tuple[float, dict]:
    """Cosine similarity of normalized whole-document embeddings → 0..1."""
    r = resume_text.strip()[:max_chars]
    j = job_text.strip()[:max_chars]
    if len(r) < 20 or len(j) < 40:
        return 0.0, {"note": "text_too_short_for_embeddings"}

    model = get_embedding_model(model_name)
    vecs = model.encode(
        [r, j],
        convert_to_numpy=True,
        normalize_embeddings=True,
        show_progress_bar=False,
    )
    sim = float(np.clip(float(np.dot(vecs[0], vecs[1])), 0.0, 1.0))
    return sim, {
        "embedding_model": model_name,
        "embedding_cosine_similarity": round(sim, 4),
    }


def chunk_embedding_coverage(
    resume_text: str,
    job_text: str,
    model_name: str,
    max_chunks: int = 14,
    chunk_size: int = 420,
) -> tuple[float, dict]:
    """
    Blend mean and min cosine between resume windows and the JD embedding.
    Penalizes resumes that only partially align with the posting.
    """
    r = resume_text.strip()
    j = job_text.strip()[:12000]
    if len(r) < 40 or len(j) < 40:
        return 0.0, {"note": "too_short"}

    chunks: list[str] = []
    for i in range(0, len(r), chunk_size):
        part = r[i : i + chunk_size].strip()
        if len(part) > 30:
            chunks.append(part)
        if len(chunks) >= max_chunks:
            break
    if not chunks:
        return 0.0, {"note": "no_chunks"}

    model = get_embedding_model(model_name)
    jd_vec = model.encode(
        [j],
        convert_to_numpy=True,
        normalize_embeddings=True,
        show_progress_bar=False,
    )[0]
    chunk_vecs = model.encode(
        chunks,
        convert_to_numpy=True,
        normalize_embeddings=True,
        show_progress_bar=False,
    )
    sims = chunk_vecs @ jd_vec
    worst = float(np.min(sims))
    mean = float(np.mean(sims))
    best = float(np.max(sims))
    # Mean + worst catches shallow fit; best rewards at least one strongly aligned block.
    blended = float(np.clip(0.52 * mean + 0.30 * worst + 0.18 * best, 0.0, 1.0))
    return blended, {
        "chunk_count": len(chunks),
        "chunk_cosine_mean": round(mean, 4),
        "chunk_cosine_min": round(worst, 4),
        "chunk_cosine_max": round(best, 4),
    }
