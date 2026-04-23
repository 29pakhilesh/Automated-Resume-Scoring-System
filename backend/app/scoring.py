"""Resume scoring: format heuristics + NLP-style alignment with job description."""

from dataclasses import dataclass

import numpy as np
from sklearn.feature_extraction.text import CountVectorizer, TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from app.bm25_scorer import score_bm25_alignment
from app.config import get_settings
from app.embeddings import chunk_embedding_coverage, embedding_similarity
from app.explanations import build_improvement_plan
from app.gap_analysis import build_gap_report
from app.reference_format import format_feedback_hints, score_format_against_reference
from app.tokens import important_tokens


def _keyword_recall_score(jd_tokens: set[str], resume_tokens: set[str]) -> tuple[float, int, int, int]:
    """Return (score_0_100, n_jd, recall_denom, n_matched)."""
    if not jd_tokens:
        return 50.0, 0, 0, 0
    matched = jd_tokens & resume_tokens
    n_jd = len(jd_tokens)
    recall_denom = max(1, min(n_jd, 52))
    ratio = len(matched) / recall_denom
    score = min(100.0, ratio * 122 + 4.0)
    return score, n_jd, recall_denom, len(matched)


def score_keyword_overlap(
    resume: str,
    job_description: str,
    position_title: str = "",
) -> tuple[float, dict]:
    """Share of substantive JD + title terms in the resume (0–100).

    Long postings: capped denominator for JD recall. **Role title** terms are scored
    separately and blended so a tailored headline is rewarded even when the JD body is long.
    """
    resume_tokens = important_tokens(resume)
    jd_tokens = important_tokens(job_description)
    jd_score, n_jd, recall_denom, n_matched = _keyword_recall_score(jd_tokens, resume_tokens)

    title = position_title.strip()
    title_tokens = important_tokens(title) if title else set()
    if title_tokens:
        title_score, n_t, _, n_t_matched = _keyword_recall_score(title_tokens, resume_tokens)
        # Title is a hard signal for intent match; blend into final keyword channel input.
        score = round(min(100.0, 0.74 * jd_score + 0.26 * title_score), 1)
    else:
        title_score = jd_score
        n_t = n_t_matched = 0
        score = round(jd_score, 1)

    return score, {
        "jd_term_count": n_jd,
        "jd_recall_denominator_capped": recall_denom,
        "matched_term_count": n_matched,
        "sample_matched": sorted(jd_tokens & resume_tokens)[:25],
        "title_term_count": len(title_tokens),
        "title_matched_term_count": n_t_matched if title_tokens else 0,
        "title_keyword_score_0_100": round(title_score, 1) if title_tokens else None,
        "jd_body_keyword_score_0_100": round(jd_score, 1),
    }


def _tfidf_cosine_two_docs(a: str, b: str) -> float:
    vectorizer = TfidfVectorizer(
        max_features=8000,
        ngram_range=(1, 3),
        min_df=1,
        strip_accents="unicode",
        lowercase=True,
    )
    try:
        matrix = vectorizer.fit_transform([a, b])
    except ValueError:
        return 0.0
    sim = cosine_similarity(matrix[0:1], matrix[1:2])[0][0]
    return float(np.clip(sim, 0.0, 1.0))


def _binary_unigram_cosine(a: str, b: str) -> float:
    cv = CountVectorizer(
        binary=True,
        lowercase=True,
        token_pattern=r"(?u)\b\w\w+\b",
    )
    try:
        matrix = cv.fit_transform([a, b])
    except ValueError:
        return 0.0
    sim = cosine_similarity(matrix[0:1], matrix[1:2])[0][0]
    return float(np.clip(sim, 0.0, 1.0))


def _char_wb_trigram_cosine(a: str, b: str) -> float:
    """Word-boundary character trigrams: robust when stacks align but wording differs."""
    cv = CountVectorizer(
        analyzer="char_wb",
        ngram_range=(3, 3),
        binary=True,
        max_features=12000,
    )
    try:
        matrix = cv.fit_transform([a, b])
    except ValueError:
        return 0.0
    sim = cosine_similarity(matrix[0:1], matrix[1:2])[0][0]
    return float(np.clip(sim, 0.0, 1.0))


def _lexical_semantic_score(resume: str, job_description: str) -> tuple[float, dict]:
    """
    Lexical-only similarity (0–100): TF–IDF + word overlap + char n-grams.
    Short resume vs long JD is handled better than TF–IDF alone, but still not 'meaning' aware.
    """
    r, j = resume.strip(), job_description.strip()
    if len(r) < 30 or len(j) < 30:
        return 0.0, {"note": "text_too_short_for_reliable_similarity"}

    tfidf_sim = _tfidf_cosine_two_docs(r, j)
    bow_sim = _binary_unigram_cosine(r, j)
    char_sim = _char_wb_trigram_cosine(r, j)

    combined01 = float(np.clip(0.18 * tfidf_sim + 0.20 * bow_sim + 0.62 * char_sim, 0.0, 1.0))
    score = round(combined01 * 100, 1)
    return score, {
        "tfidf_cosine_similarity": round(tfidf_sim, 4),
        "unigram_binary_cosine": round(bow_sim, 4),
        "char_wb_trigram_cosine": round(char_sim, 4),
        "lexical_blended_0_1": round(combined01, 4),
        "lexical_note": (
            "Lexical channel blends TF–IDF, word overlap, and character n-grams (surface similarity)."
        ),
    }


def score_semantic_alignment(
    resume: str,
    job_description: str,
    *,
    embedding_model: str | None = None,
) -> tuple[float, dict]:
    """
    Semantic fit (0–100): combines sentence-transformer embeddings with lexical channels.
    Embeddings capture paraphrase/meaning overlap better than bag-of-words alone.
    """
    settings = get_settings()
    model = embedding_model or settings.embedding_model

    r, j = resume.strip(), job_description.strip()
    if len(r) < 30 or len(j) < 30:
        return 0.0, {"note": "text_too_short_for_reliable_similarity"}

    lex_score, lex_detail = _lexical_semantic_score(r, j)
    try:
        doc_sim, emb_doc = embedding_similarity(r, j, model)
        chunk01, emb_chunk = chunk_embedding_coverage(r, j, model)
        emb01 = float(np.clip(0.64 * doc_sim + 0.36 * chunk01, 0.0, 1.0))
        emb_score = emb01 * 100.0
        combined = float(np.clip(0.62 * emb_score + 0.38 * lex_score, 0.0, 100.0))
        detail: dict = {
            **lex_detail,
            **emb_doc,
            **emb_chunk,
            "embedding_blend_0_1": round(emb01, 4),
            "embedding_score_0_100": round(emb_score, 1),
            "lexical_score_0_100": lex_score,
            "semantic_note": (
                "Semantic fit blends transformer embeddings (meaning) with lexical channels (exact/stack overlap)."
            ),
        }
        return round(combined, 1), detail
    except Exception as exc:  # noqa: BLE001
        detail = {
            **lex_detail,
            "embedding_error": str(exc)[:500],
            "semantic_note": "Embeddings unavailable; scored using lexical channel only.",
        }
        return lex_score, detail


@dataclass
class ScoreWeights:
    # Favor JD alignment (semantic + keywords) over strict template match.
    format: float = 0.18
    semantic: float = 0.50
    keywords: float = 0.32


def compute_overall_score(
    format_score: float,
    semantic_score: float,
    keyword_score: float,
    weights: ScoreWeights | None = None,
) -> float:
    w = weights or ScoreWeights()
    total_w = w.format + w.semantic + w.keywords
    combined = (
        w.format * format_score + w.semantic * semantic_score + w.keywords * keyword_score
    ) / total_w
    return round(min(100.0, max(0.0, combined)), 1)


def score_resume(
    resume_text: str,
    job_description: str,
    position_title: str,
    weights: ScoreWeights | None = None,
) -> dict:
    """Full scoring payload for API response."""
    w = weights or ScoreWeights()
    settings = get_settings()

    jd_combined = f"{position_title.strip()}\n\n{job_description.strip()}".strip()
    jd_body = job_description.strip()
    title_clean = position_title.strip()
    fmt, fmt_detail = score_format_against_reference(resume_text)
    sem, sem_detail = score_semantic_alignment(
        resume_text,
        jd_combined,
        embedding_model=settings.embedding_model,
    )
    kw_overlap, kw_detail = score_keyword_overlap(resume_text, jd_body, title_clean)
    bm25, bm25_detail = score_bm25_alignment(resume_text, jd_combined)
    kw = round(min(100.0, 0.52 * kw_overlap + 0.48 * bm25), 1)
    kw_detail = {
        **kw_detail,
        "keyword_overlap_base_0_100": kw_overlap,
        "bm25_alignment_0_100": bm25,
        "bm25_detail": bm25_detail,
        "keyword_note": "Keyword fit blends exact important-token recall with BM25 sentence relevance to the JD.",
    }
    overall = compute_overall_score(fmt, sem, kw, w)

    format_hints = format_feedback_hints(fmt_detail)
    wc = int(fmt_detail.get("word_count") or 0)
    gap_report = build_gap_report(
        resume_text,
        jd_combined,
        fmt_detail=fmt_detail,
        kw_detail=kw_detail,
        sem_detail=sem_detail,
        embedding_model=settings.embedding_model,
    )
    feedback: list[str] = []
    if wc < 110:
        feedback.append(
            "Very little text was extracted from your file. Image-heavy or scanned PDFs often produce "
            "low keyword and semantic scores even with a strong job description—try a text-based PDF or DOCX."
        )
    feedback.extend(format_hints)
    if 110 <= wc < 150:
        feedback.append("Resume text is fairly short; add more concrete accomplishments and context.")
    if kw_detail.get("matched_term_count", 0) < max(3, kw_detail.get("jd_term_count", 0) // 10):
        feedback.append("Mirror more language from the job description (tools, domains, responsibilities) where truthful.")

    if not feedback:
        feedback.append("Strong alignment signals overall; keep tailoring for each role.")

    improvement_plan = build_improvement_plan(
        overall=overall,
        fmt=fmt,
        sem=sem,
        kw=kw,
        gap_report=gap_report,
        format_hints=format_hints,
    )

    return {
        "overall_score": overall,
        "subscores": {
            "format_and_structure": fmt,
            "semantic_fit_vs_job_description": sem,
            "keyword_coverage_vs_job_description": kw,
        },
        "weights_applied": {"format": w.format, "semantic": w.semantic, "keywords": w.keywords},
        "details": {
            "format": fmt_detail,
            "semantic": sem_detail,
            "keywords": kw_detail,
        },
        "gap_report": gap_report,
        "improvement_plan": improvement_plan,
        "position_title_considered": position_title.strip(),
        "feedback": feedback[:6],
    }
