"""In-memory async scoring jobs with progress (no disk persistence of uploads)."""

from __future__ import annotations

import asyncio
import time
import uuid
from dataclasses import dataclass, field
from typing import Any


@dataclass
class JobEvent:
    ts: float
    type: str  # "progress" | "result" | "error"
    data: dict[str, Any]


@dataclass
class ScoringJob:
    id: str
    created_at: float
    events: list[JobEvent] = field(default_factory=list)
    done: bool = False

    def emit(self, type: str, data: dict[str, Any]) -> None:
        self.events.append(JobEvent(ts=time.time(), type=type, data=data))


class ScoringJobManager:
    def __init__(self, *, ttl_seconds: int = 15 * 60, max_jobs: int = 200) -> None:
        self._ttl = ttl_seconds
        self._max = max_jobs
        self._jobs: dict[str, ScoringJob] = {}
        self._lock = asyncio.Lock()

    async def create(self) -> ScoringJob:
        async with self._lock:
            self._gc_locked()
            if len(self._jobs) >= self._max:
                # Drop oldest job(s) to keep memory bounded.
                for jid, _ in sorted(self._jobs.items(), key=lambda kv: kv[1].created_at)[:5]:
                    self._jobs.pop(jid, None)
            jid = uuid.uuid4().hex
            job = ScoringJob(id=jid, created_at=time.time())
            self._jobs[jid] = job
            return job

    async def get(self, job_id: str) -> ScoringJob | None:
        async with self._lock:
            self._gc_locked()
            return self._jobs.get(job_id)

    async def append(self, job_id: str, type: str, data: dict[str, Any]) -> None:
        async with self._lock:
            self._gc_locked()
            job = self._jobs.get(job_id)
            if not job:
                return
            job.emit(type, data)
            if type in {"result", "error"}:
                job.done = True

    def _gc_locked(self) -> None:
        now = time.time()
        expired = [jid for jid, j in self._jobs.items() if (now - j.created_at) > self._ttl]
        for jid in expired:
            self._jobs.pop(jid, None)


# singleton used by API routes
JOB_MANAGER = ScoringJobManager()

