"""Orchestration layer: scoring + Python coach + persistence (all Python)."""

from __future__ import annotations

from typing import Any

import anyio

from app.coach_python import build_python_coach
from app.config import get_settings
from app.db.crud import save_scoring_run
from app.db.session import get_session_factory
from app.explanations import openai_coach_explanation
from app.scoring import score_resume
from app.scoring_privacy import scoring_run_payload_for_db


async def score_resume_pipeline(
    *,
    resume_text: str,
    job_description: str,
    position_title: str,
    filename: str,
    extracted_preview_len: int = 800,
) -> dict[str, Any]:
    """
    End-to-end scoring used by the API:
    - CPU-heavy scoring in a worker thread
    - Always attaches a **Python-only** coach narrative
    - Optionally attaches a remote coach if explicitly enabled in settings
    - Persistence: uploads are never written to disk. DB rows are off by default
      (`PERSIST_SCORING_RUNS=false`). When persistence is on, `STORE_SCORING_SENSITIVE_CONTENT_IN_DB`
      defaults to false so JD excerpts, upload filenames, and full payloads are not stored.
    """
    settings = get_settings()
    result = await anyio.to_thread.run_sync(score_resume, resume_text, job_description, position_title)
    result["filename"] = filename
    preview = resume_text.strip()
    result["extracted_text_preview"] = preview[:extracted_preview_len] + (
        "…" if len(preview) > extracted_preview_len else ""
    )

    coach_ctx: dict[str, Any] = {
        "overall_score": result.get("overall_score"),
        "subscores": result.get("subscores"),
        "improvement_plan": result.get("improvement_plan"),
        "missing_keywords": (result.get("gap_report") or {}).get("missing_keywords_from_jd", [])[:45],
        "weakest_segments": (result.get("gap_report") or {}).get("weakest_resume_segments_vs_jd", [])[:4],
        "resume_preview": preview[:3500],
        "jd_preview": job_description.strip()[:3500],
        "position_title": position_title.strip(),
    }

    result["ai_coach"] = build_python_coach(coach_ctx)

    if settings.enable_openai_coach and settings.openai_api_key:
        remote = await openai_coach_explanation(settings=settings, context=coach_ctx)
        if remote and remote.get("text"):
            result["ai_coach_remote"] = {
                "provider": remote.get("provider"),
                "model": remote.get("model"),
                "text": remote["text"],
            }
        elif remote and remote.get("error"):
            result["ai_coach_remote"] = {"error": remote.get("error"), "model": remote.get("model")}

    if settings.persist_scoring_runs:
        jd_excerpt = (
            job_description.strip()[:4000]
            if settings.store_scoring_sensitive_content_in_db
            else ""
        )
        filename_for_db = (
            filename if settings.store_scoring_sensitive_content_in_db else ""
        )
        payload = scoring_run_payload_for_db(
            result,
            store_sensitive=settings.store_scoring_sensitive_content_in_db,
        )
        try:
            factory = get_session_factory()
            async with factory() as session:
                await save_scoring_run(
                    session,
                    filename=filename_for_db,
                    position_title=position_title.strip(),
                    jd_excerpt=jd_excerpt,
                    overall_score=float(result["overall_score"]),
                    format_score=float(result["subscores"]["format_and_structure"]),
                    semantic_score=float(result["subscores"]["semantic_fit_vs_job_description"]),
                    keyword_score=float(result["subscores"]["keyword_coverage_vs_job_description"]),
                    payload=payload,
                )
        except Exception:
            pass

    return result
