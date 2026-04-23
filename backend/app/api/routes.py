from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from app.dataset import load_job_archetypes
from app.db.queries import list_recent_runs
from app.db.session import get_session_factory
from app.parsers import extract_resume_text
from app.services.scoring_service import score_resume_pipeline

router = APIRouter(prefix="/api")

MAX_UPLOAD_BYTES = 5 * 1024 * 1024


@router.get("/health")
def health() -> dict:
    return {"status": "ok", "version": "0.4.0", "backend": "python"}


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
    if not position_title or not position_title.strip():
        raise HTTPException(status_code=400, detail="position_title is required")
    if not job_description or len(job_description.strip()) < 40:
        raise HTTPException(
            status_code=400,
            detail="job_description should be at least 40 characters for meaningful scoring",
        )

    name = file.filename or ""
    if not (name.lower().endswith(".pdf") or name.lower().endswith(".docx")):
        raise HTTPException(status_code=400, detail="Upload a PDF or DOCX file")

    data = await file.read()
    if len(data) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=400, detail="File too large (max 5 MB)")

    try:
        text = extract_resume_text(name, data)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=422, detail=f"Could not read resume: {exc}") from exc

    if not text or len(text.strip()) < 50:
        raise HTTPException(
            status_code=422,
            detail="Very little text extracted. Try another PDF (text-based, not only scanned images) or DOCX.",
        )

    return await score_resume_pipeline(
        resume_text=text,
        job_description=job_description,
        position_title=position_title,
        filename=name,
    )
