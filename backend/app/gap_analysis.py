"""Deterministic gap detection: missing JD language, weak resume chunks vs JD, format gaps."""

from __future__ import annotations

import re
from typing import Any

from app.embeddings import get_embedding_model
from app.tokens import important_tokens

EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")
PHONE_RE = re.compile(r"(?:(?:\+?\d{1,3}[\s-]?)?(?:\(\d{2,4}\)[\s-]?)?\d{3}[\s-]?\d{3}[\s-]?\d{4})")
LINK_RE = re.compile(r"(https?://\S+|www\.\S+)", re.IGNORECASE)


def _looks_like_contact_or_header(text: str) -> bool:
    t = text.strip()
    if not t:
        return False
    if EMAIL_RE.search(t) or PHONE_RE.search(t):
        return True
    # common resume header/link markers
    if LINK_RE.search(t) and ("linkedin" in t.lower() or "github" in t.lower()):
        return True
    return False


def missing_jd_terms(resume_text: str, jd_text: str, limit: int = 35) -> list[str]:
    """Important JD tokens absent from the resume (substring match, lowercase)."""
    jd_tokens = important_tokens(jd_text)
    blob = resume_text.lower()
    missing = [t for t in jd_tokens if t not in blob]
    missing.sort(key=lambda t: (len(t), t), reverse=True)
    return missing[:limit]


def weakest_resume_spans(
    resume_text: str,
    jd_text: str,
    model_name: str,
    chunk_size: int = 420,
    max_chunks: int = 14,
) -> list[dict[str, Any]]:
    """Return lowest-cosine resume chunks vs whole JD (where content alignment is weakest)."""
    r = resume_text.strip()
    j = jd_text.strip()[:12000]
    if len(r) < 60 or len(j) < 60:
        return []

    chunks: list[tuple[int, str]] = []
    for i in range(0, len(r), chunk_size):
        part = r[i : i + chunk_size].strip()
        if len(part) > 40:
            chunks.append((i, part))
        if len(chunks) >= max_chunks:
            break
    if not chunks:
        return []

    try:
        model = get_embedding_model(model_name)
        jd_vec = model.encode(
            [j],
            convert_to_numpy=True,
            normalize_embeddings=True,
            show_progress_bar=False,
        )[0]
        texts = [c[1] for c in chunks]
        vecs = model.encode(
            texts,
            convert_to_numpy=True,
            normalize_embeddings=True,
            show_progress_bar=False,
        )
        sims = (vecs @ jd_vec).tolist()
    except Exception:  # noqa: BLE001
        return []

    ranked = sorted(
        [{"offset": chunks[i][0], "preview": _preview(chunks[i][1]), "cosine": round(float(sims[i]), 4)} for i in range(len(chunks))],
        key=lambda x: x["cosine"],
    )
    # Avoid leaking contact/header info in previews (emails, phone, links).
    out: list[dict[str, Any]] = []
    for item in ranked:
        prev = str(item.get("preview") or "")
        if _looks_like_contact_or_header(prev):
            continue
        out.append(item)
        if len(out) >= 4:
            break
    return out


def _preview(text: str, max_len: int = 160) -> str:
    one = re.sub(r"\s+", " ", text).strip()
    # Redact contact-like strings (extra safety).
    one = EMAIL_RE.sub("[redacted email]", one)
    one = PHONE_RE.sub("[redacted phone]", one)
    return one if len(one) <= max_len else one[: max_len - 1] + "…"


def build_gap_report(
    resume_text: str,
    jd_combined: str,
    *,
    fmt_detail: dict,
    kw_detail: dict,
    sem_detail: dict,
    embedding_model: str,
) -> dict[str, Any]:
    missing = missing_jd_terms(resume_text, jd_combined)
    weak = weakest_resume_spans(resume_text, jd_combined, embedding_model)
    return {
        "missing_keywords_from_jd": missing,
        "weakest_resume_segments_vs_jd": weak,
        "keyword_stats": {
            "jd_term_count": kw_detail.get("jd_term_count"),
            "matched_term_count": kw_detail.get("matched_term_count"),
        },
        "semantic_signals": {
            "char_wb_trigram_cosine": sem_detail.get("char_wb_trigram_cosine"),
            "embedding_cosine": sem_detail.get("embedding_cosine_similarity"),
            "chunk_cosine_min": sem_detail.get("chunk_cosine_min"),
            "chunk_cosine_max": sem_detail.get("chunk_cosine_max"),
        },
        "format_highlights": {
            "sections_found": list((fmt_detail.get("sections_found") or {}).keys()),
            "word_count": fmt_detail.get("word_count"),
        },
    }
