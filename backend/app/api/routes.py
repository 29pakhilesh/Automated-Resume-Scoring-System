import asyncio
import logging
import time
import json

import anyio
from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import Response, StreamingResponse

from app.dataset import load_job_archetypes
from app.db.queries import list_recent_runs
from app.db.session import get_session_factory
from app.parsers import extract_resume_text
from app.services.scoring_jobs import JOB_MANAGER
from app.services.scoring_service import score_resume_pipeline
from app.snippet_store import SNIPPET_STORE

router = APIRouter(prefix="/api")

MAX_UPLOAD_BYTES = 5 * 1024 * 1024

log = logging.getLogger("rss.api")

def _sse(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


@router.get("/health")
def health() -> dict:
    from app.config import get_settings

    s = get_settings()
    return {
        "status": "ok",
        "version": "0.4.0",
        "backend": "python",
        "scoring_weights": {
            "format": s.scoring_weight_format,
            "semantic": s.scoring_weight_semantic,
            "keywords": s.scoring_weight_keywords,
        },
    }


@router.get("/snippet/{token}.png")
def snippet_png(token: str) -> Response:
    """Serve a short-lived snippet PNG generated during scoring."""
    # tolerate callers appending .png twice
    tok = token.removesuffix(".png")
    png = SNIPPET_STORE.get(tok)
    if not png:
        raise HTTPException(status_code=404, detail="Snippet not found (expired) or invalid token")
    return Response(
        content=png,
        media_type="image/png",
        headers={"Cache-Control": "no-store"},
    )


@router.get("/archetypes")
def archetypes() -> dict:
    rows = load_job_archetypes()
    return {
        "count": len(rows),
        "items": [{"id": r.id, "title": r.title, "tags": list(r.tags), "jd": r.jd} for r in rows],
    }


@router.get("/runs")
async def runs(limit: int = 30) -> dict:
    factory = get_session_factory()
    async with factory() as session:
        rows = await list_recent_runs(session, limit=min(max(limit, 1), 100))
    return {
        "count": len(rows),
        "items": [
            {
                "id": r.id,
                "created_at": r.created_at.isoformat() if r.created_at else None,
                "filename": r.filename,
                "position_title": r.position_title,
                "overall_score": r.overall_score,
                "format_score": r.format_score,
                "semantic_score": r.semantic_score,
                "keyword_score": r.keyword_score,
            }
            for r in rows
        ],
    }


@router.post("/score")
async def score_endpoint(
    file: UploadFile = File(...),
    job_description: str = Form(...),
    position_title: str = Form(...),
) -> dict:
    t0 = time.monotonic()
    if not position_title or not position_title.strip():
        raise HTTPException(status_code=400, detail="position_title is required")
    if not job_description or len(job_description.strip()) < 40:
        raise HTTPException(
            status_code=400,
            detail="job_description should be at least 40 characters for meaningful scoring",
        )

    name = file.filename or ""
    if not (
        name.lower().endswith((".pdf", ".docx", ".png", ".jpg", ".jpeg", ".webp"))
    ):
        raise HTTPException(status_code=400, detail="Upload a PDF, DOCX, PNG, JPG, or WEBP file")

    data = await file.read()
    if len(data) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=400, detail="File too large (max 5 MB)")

    log.info("score:start filename=%r bytes=%d title=%r", name, len(data), position_title.strip()[:120])
    try:
        text = await anyio.to_thread.run_sync(extract_resume_text, name, data)
    except Exception as exc:  # noqa: BLE001
        log.info("score:extract_failed filename=%r err=%r", name, str(exc)[:200])
        raise HTTPException(status_code=422, detail=f"Could not read resume: {exc}") from exc

    if not text or len(text.strip()) < 50:
        log.info("score:too_little_text filename=%r extracted_len=%d", name, len((text or "").strip()))
        raise HTTPException(
            status_code=422,
            detail="Very little text extracted. Try another PDF (text-based, not only scanned images) or DOCX.",
        )

    try:
        out = await score_resume_pipeline(
            resume_text=text,
            job_description=job_description,
            position_title=position_title,
            filename=name,
            resume_pdf_bytes=data,
        )
        return out
    finally:
        log.info("score:done filename=%r ms=%.0f", name, (time.monotonic() - t0) * 1000)


@router.post("/score_async")
async def score_async_start(
    file: UploadFile = File(...),
    job_description: str = Form(...),
    position_title: str = Form(...),
) -> dict:
    """
    Starts a scoring job and returns a job id.
    Progress is streamed over SSE from GET /api/score_events/{job_id}.
    Upload bytes and extracted text are kept in memory only for the duration of the job.
    """
    if not position_title or not position_title.strip():
        raise HTTPException(status_code=400, detail="position_title is required")
    if not job_description or len(job_description.strip()) < 40:
        raise HTTPException(
            status_code=400,
            detail="job_description should be at least 40 characters for meaningful scoring",
        )

    name = file.filename or ""
    if not (
        name.lower().endswith((".pdf", ".docx", ".png", ".jpg", ".jpeg", ".webp"))
    ):
        raise HTTPException(status_code=400, detail="Upload a PDF, DOCX, PNG, JPG, or WEBP file")

    data = await file.read()
    if len(data) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=400, detail="File too large (max 5 MB)")

    job = await JOB_MANAGER.create()
    await JOB_MANAGER.append(job.id, "progress", {"step": "upload_received", "message": "Upload received", "pct": 5})

    async def _run() -> None:
        t0 = time.monotonic()
        try:
            await JOB_MANAGER.append(job.id, "progress", {"step": "extracting_text", "message": "Extracting text", "pct": 18})
            text = await anyio.to_thread.run_sync(extract_resume_text, name, data)
            if not text or len(text.strip()) < 50:
                raise ValueError(
                    "Very little text extracted. Try another PDF (text-based, not only scanned images) or DOCX."
                )

            await JOB_MANAGER.append(job.id, "progress", {"step": "scoring", "message": "Scoring and matching to job description", "pct": 55})
            out = await score_resume_pipeline(
                resume_text=text,
                job_description=job_description,
                position_title=position_title,
                filename=name,
                resume_pdf_bytes=data,
            )
            await JOB_MANAGER.append(job.id, "progress", {"step": "finalizing", "message": "Finalizing results", "pct": 95})
            await JOB_MANAGER.append(
                job.id,
                "result",
                {"result": out, "ms": int((time.monotonic() - t0) * 1000)},
            )
        except Exception as exc:  # noqa: BLE001
            # Named "joberror" (not "error") so browser EventSource clients don't confuse it with transport errors.
            await JOB_MANAGER.append(job.id, "joberror", {"message": str(exc)[:600]})

    # Fire-and-forget background job
    asyncio.create_task(_run())
    return {"job_id": job.id}


@router.get("/score_events/{job_id}")
async def score_events(job_id: str):
    """Server-Sent Events stream for a scoring job."""

    async def gen():
        last_idx = 0
        last_keepalive = time.monotonic()
        # Initial ping so EventSource opens reliably behind proxies.
        yield _sse("progress", {"step": "connected", "message": "Connected", "pct": 1})
        while True:
            job = await JOB_MANAGER.get(job_id)
            if job is None:
                yield _sse("joberror", {"message": "Job not found (expired). Please try again."})
                return

            # Stream any new events
            events = job.events
            while last_idx < len(events):
                ev = events[last_idx]
                last_idx += 1
                yield _sse(ev.type, ev.data)
                if ev.type in {"result", "joberror"}:
                    return

            # Keep-alive: SSE comment frames keep intermediaries from closing idle streams.
            now = time.monotonic()
            if now - last_keepalive > 12:
                yield ": ping\n\n"
                last_keepalive = now

            # Keep-alive
            await asyncio.sleep(0.25)

    headers = {
        # Help proxies (Render/Cloudflare) stream chunks instead of buffering SSE.
        "Cache-Control": "no-cache, no-transform",
        "Connection": "keep-alive",
        "X-Accel-Buffering": "no",
    }
    return StreamingResponse(gen(), media_type="text/event-stream", headers=headers)
