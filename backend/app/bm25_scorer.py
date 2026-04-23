"""BM25 retrieval signal: how well resume sentences explain JD query terms (pure Python / NumPy)."""

from __future__ import annotations

import re

import numpy as np
from rank_bm25 import BM25Okapi


def _tokenize(text: str) -> list[str]:
    return re.findall(r"[a-z0-9+#.]+", text.lower())


def _sentences(text: str) -> list[str]:
    parts = re.split(r"(?<=[.!?])\s+|\n+", text)
    return [p.strip() for p in parts if len(p.strip()) > 18]


def score_bm25_alignment(resume: str, jd: str) -> tuple[float, dict]:
    """
    Score 0–100: BM25 relevance of resume sentence corpus to JD-derived query tokens.
    Complements exact token overlap by rewarding strong local matches in specific bullets.
    """
    r = resume.strip()
    j = jd.strip()
    if len(r) < 40 or len(j) < 40:
        return 0.0, {"note": "too_short"}

    sents = _sentences(r)
    if not sents:
        sents = [r[:4000]]

    corpus: list[list[str]] = []
    for s in sents:
        toks = _tokenize(s)
        if len(toks) >= 5:
            corpus.append(toks)
    if not corpus:
        return 0.0, {"note": "resume_token_sparse"}

    query = [t for t in _tokenize(j) if len(t) > 2]
    if len(query) < 8:
        return 50.0, {"note": "jd_query_short"}

    bm25 = BM25Okapi(corpus)
    scores = bm25.get_scores(query)
    if scores is None or len(scores) == 0:
        return 0.0, {"note": "bm25_failed"}

    arr = np.asarray(scores, dtype=float)
    k = min(5, arr.size)
    top_mean = float(np.sort(arr)[-k:].mean())
    # Soft squash: BM25 raw scale varies; log mapping keeps outliers sane.
    mapped = float(min(100.0, 26.0 * np.log1p(max(0.0, top_mean))))
    return round(mapped, 1), {
        "bm25_top_mean_raw": round(top_mean, 4),
        "bm25_resume_sentence_count": int(arr.size),
        "bm25_query_token_count": len(query),
    }
