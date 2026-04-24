"""Orchestration layer: scoring + Python coach + persistence (all Python)."""

from __future__ import annotations

from typing import Any

import anyio

from app.coach_python import build_python_coach
from app.config import get_settings
from app.db.crud import save_scoring_run
from app.db.session import get_session_factory
from app.scoring import score_resume
from app.scoring_privacy import scoring_run_payload_for_db
from app.snippet_image import (
    render_file_annotated_preview_png,
    render_file_snippet_png,
    render_text_highlight_preview_png,
)
from app.snippet_store import SNIPPET_STORE


async def score_resume_pipeline(
    *,
    resume_text: str,
    job_description: str,
    position_title: str,
    filename: str,
    resume_pdf_bytes: bytes | None = None,
    extracted_preview_len: int = 800,
) -> dict[str, Any]:
    """
    End-to-end scoring used by the API:
    - CPU-heavy scoring in a worker thread
    - Always attaches a **Python-only** coach narrative
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

    def _y_ratio_for_chunk(*, resume: str, offset: int, chunk_text: str | None) -> float:
        n = max(1, len(resume))
        start = int(offset) if offset is not None else 0
        start = max(0, min(n - 1, start))
        if chunk_text:
            needle = chunk_text.strip()
            if len(needle) >= 24:
                at = resume.find(needle)
                if at != -1:
                    start = at
        # bias slightly downward so headings aren't always centered awkwardly
        center = start + min(220, max(40, n // 18))
        return min(0.92, max(0.08, center / n))

    # Best-effort: preview images (always attempt when bytes are available).
    if resume_pdf_bytes:
        plan = result.get("improvement_plan") or []
        gap = result.get("gap_report") or {}
        weak = [w for w in (gap.get("weakest_resume_segments_vs_jd") or []) if isinstance(w, dict)]
        w0 = weak[0] if weak else None

        shared_url: str | None = None
        try:
            ann_png = await anyio.to_thread.run_sync(
                render_file_annotated_preview_png,
                filename,
                resume_pdf_bytes,
                resume_text=preview,
                weak_segments=weak,
            )
            token = SNIPPET_STORE.put(ann_png)
            shared_url = f"/api/snippet/{token}.png"
            result["annotated_document_preview"] = {
                "mime": "image/png",
                "url": shared_url,
                "marked_regions": len(weak),
            }
        except Exception:
            # Hard fallback: generate a text-based PNG so the UI always has *some* preview.
            try:
                fallback = await anyio.to_thread.run_sync(
                    render_text_highlight_preview_png,
                    resume_text=preview,
                    weak_segments=weak,
                )
                token = SNIPPET_STORE.put(fallback)
                shared_url = f"/api/snippet/{token}.png"
                result["annotated_document_preview"] = {
                    "mime": "image/png",
                    "url": shared_url,
                    "marked_regions": len(weak),
                }
            except Exception:
                result.pop("annotated_document_preview", None)

        if shared_url:
            ws: dict[str, Any] = {"mime": "image/png", "url": shared_url}
            if w0:
                ws["offset"] = w0.get("offset")
                ws["cosine"] = w0.get("cosine")
            result["weak_section_snippet"] = ws

            for item in plan:
                if not isinstance(item, dict):
                    continue
                if item.get("area") != "semantic_fit_vs_job_description":
                    continue
                sn = item.get("snippet") or {}
                if not isinstance(sn, dict) or sn.get("kind") != "resume_pdf_band":
                    continue
                item["snippet_image_mime"] = "image/png"
                item["snippet_image_url"] = shared_url
                item["snippet_full_document_preview"] = True
                item.pop("snippet_image_base64", None)
        else:
            # Fallback: vertical band on first page only.
            if w0:
                off = w0.get("offset")
                try:
                    off_i = int(off) if off is not None else 0
                except Exception:  # noqa: BLE001
                    off_i = 0
                chunk_txt = w0.get("preview")
                chunk_txt_s = str(chunk_txt) if chunk_txt is not None else ""
                y_ratio = _y_ratio_for_chunk(resume=preview, offset=off_i, chunk_text=chunk_txt_s)
                try:
                    png = await anyio.to_thread.run_sync(
                        render_file_snippet_png,
                        filename,
                        resume_pdf_bytes,
                        y_center_ratio=y_ratio,
                    )
                    token = SNIPPET_STORE.put(png)
                    result["weak_section_snippet"] = {
                        "mime": "image/png",
                        "url": f"/api/snippet/{token}.png",
                        "offset": w0.get("offset"),
                        "cosine": w0.get("cosine"),
                    }
                except Exception:
                    # Final fallback: text-based PNG
                    try:
                        fallback = await anyio.to_thread.run_sync(
                            render_text_highlight_preview_png,
                            resume_text=preview,
                            weak_segments=weak,
                        )
                        token = SNIPPET_STORE.put(fallback)
                        result["weak_section_snippet"] = {
                            "mime": "image/png",
                            "url": f"/api/snippet/{token}.png",
                            "offset": w0.get("offset") if w0 else None,
                            "cosine": w0.get("cosine") if w0 else None,
                        }
                    except Exception:
                        result.pop("weak_section_snippet", None)

            for item in plan:
                if not isinstance(item, dict):
                    continue
                if item.get("area") != "semantic_fit_vs_job_description":
                    continue
                sn = item.get("snippet") or {}
                if not isinstance(sn, dict) or sn.get("kind") != "resume_pdf_band":
                    continue
                off = sn.get("offset")
                try:
                    off_i = int(off) if off is not None else 0
                except Exception:  # noqa: BLE001
                    off_i = 0
                chunk_txt = sn.get("text_preview")
                chunk_txt_s = str(chunk_txt) if chunk_txt is not None else ""
                y_ratio = _y_ratio_for_chunk(resume=preview, offset=off_i, chunk_text=chunk_txt_s)
                try:
                    png = await anyio.to_thread.run_sync(
                        render_file_snippet_png,
                        filename,
                        resume_pdf_bytes,
                        y_center_ratio=y_ratio,
                    )
                    token = SNIPPET_STORE.put(png)
                    item["snippet_image_mime"] = "image/png"
                    item["snippet_image_url"] = f"/api/snippet/{token}.png"
                    item.pop("snippet_image_base64", None)
                except Exception:
                    item.pop("snippet_image_mime", None)
                    item.pop("snippet_image_base64", None)
                    item.pop("snippet_image_url", None)

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
