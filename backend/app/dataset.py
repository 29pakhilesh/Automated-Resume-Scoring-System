"""
Curated job archetypes (reference JD snippets + tags) for benchmarking and UI presets.
Extend `data/jd_archetypes.jsonl` as your in-house dataset grows.

Optional benchmarks: Hugging Face `app.dataset_hf` / `benchmark_hf_resume_ats.py`;
Kaggle Jobsphere `app.dataset_kaggle` / `benchmark_kaggle_jobsphere.py`.
"""

from __future__ import annotations

import json
from dataclasses import dataclass

from app.paths import DATA_DIR

ARCHETYPES_PATH = DATA_DIR / "jd_archetypes.jsonl"


@dataclass(frozen=True)
class JobArchetype:
    id: str
    title: str
    jd: str
    tags: tuple[str, ...]


def load_job_archetypes(limit: int = 500) -> list[JobArchetype]:
    path = ARCHETYPES_PATH
    if not path.is_file():
        return []
    out: list[JobArchetype] = []
    with path.open(encoding="utf-8") as f:
        for i, line in enumerate(f):
            if i >= limit:
                break
            line = line.strip()
            if not line:
                continue
            obj = json.loads(line)
            tags = obj.get("tags") or []
            out.append(
                JobArchetype(
                    id=str(obj.get("id", f"row-{i}")),
                    title=str(obj.get("title", "")),
                    jd=str(obj.get("jd", "")),
                    tags=tuple(str(t) for t in tags),
                )
            )
    return out
