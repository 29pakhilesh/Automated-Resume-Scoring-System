from datetime import datetime

from sqlalchemy import DateTime, Float, Integer, String, Text, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class ScoringRun(Base):
    """Persisted scoring events for analytics at scale (SQLite locally; Postgres in prod)."""

    __tablename__ = "scoring_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    filename: Mapped[str] = mapped_column(String(512))
    position_title: Mapped[str] = mapped_column(String(512))
    jd_excerpt: Mapped[str] = mapped_column(Text)
    overall_score: Mapped[float] = mapped_column(Float)
    format_score: Mapped[float] = mapped_column(Float)
    semantic_score: Mapped[float] = mapped_column(Float)
    keyword_score: Mapped[float] = mapped_column(Float)
    payload_json: Mapped[str] = mapped_column(Text)
