from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import ScoringRun


async def list_recent_runs(session: AsyncSession, limit: int = 50) -> list[ScoringRun]:
    q = select(ScoringRun).order_by(ScoringRun.id.desc()).limit(min(limit, 200))
    res = await session.execute(q)
    return list(res.scalars().all())
