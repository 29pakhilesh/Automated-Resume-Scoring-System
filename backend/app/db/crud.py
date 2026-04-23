import json

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import ScoringRun


async def save_scoring_run(
    session: AsyncSession,
    *,
    filename: str,
    position_title: str,
    jd_excerpt: str,
    overall_score: float,
    format_score: float,
    semantic_score: float,
    keyword_score: float,
    payload: dict,
) -> ScoringRun:
    row = ScoringRun(
        filename=filename[:500],
        position_title=position_title[:500],
        jd_excerpt=jd_excerpt[:8000],
        overall_score=overall_score,
        format_score=format_score,
        semantic_score=semantic_score,
        keyword_score=keyword_score,
        payload_json=json.dumps(payload, ensure_ascii=False)[:200_000],
    )
    session.add(row)
    await session.commit()
    await session.refresh(row)
    return row
