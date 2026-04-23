#!/usr/bin/env python3
"""
Score Kaggle **Jobsphere ATS Resume Scoring** templates (.docx / .pdf) with the same generic JD
used for the Hugging Face benchmark, and print summary stats (no per-file labels in corpus).

Requires: `pip install kagglehub`, plus `KAGGLE_USERNAME` + `KAGGLE_KEY` for first download.

Usage:
  cd backend && ../.venv/bin/python benchmark_kaggle_jobsphere.py --limit 40
"""

from __future__ import annotations

import argparse
import statistics
import sys
from pathlib import Path

import numpy as np

BACKEND_ROOT = Path(__file__).resolve().parent
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.benchmark_common import GENERIC_JD, GENERIC_TITLE  # noqa: E402
from app.dataset_kaggle import download_kaggle_dataset, iter_kaggle_docx_resume_texts, resolve_jobsphere_slug  # noqa: E402
from app.scoring import score_resume  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser(description="Score Jobsphere Kaggle .docx resumes (generic JD).")
    ap.add_argument("--slug", default=None, help="Kaggle dataset slug (default: mohamedramadan2040/jobsphere-ats-resume-scoring)")
    ap.add_argument("--limit", type=int, default=50, help="Max resume files to score (0 = no limit)")
    args = ap.parse_args()

    slug = resolve_jobsphere_slug(args.slug)
    print(f"Downloading / resolving: {slug}", flush=True)
    root = download_kaggle_dataset(slug)
    print(f"Dataset root: {root}", flush=True)

    lim = None if args.limit == 0 else args.limit
    scores: list[float] = []
    for name, text in iter_kaggle_docx_resume_texts(root, limit=lim):
        out = score_resume(text, GENERIC_JD, GENERIC_TITLE)
        scores.append(float(out["overall_score"]))
        if len(scores) % 10 == 0:
            print(f"  scored {len(scores)} …", flush=True)

    if len(scores) < 1:
        print("No resume files produced extractable text.", file=sys.stderr)
        return 1

    arr = np.asarray(scores, dtype=np.float64)
    print("\n--- Jobsphere (generic JD) ---")
    print(f"n_files_scored: {len(scores)}")
    print(f"mean overall:  {float(arr.mean()):.2f}")
    print(f"std overall:   {float(arr.std()):.2f}")
    print(f"min / max:     {float(arr.min()):.1f} / {float(arr.max()):.1f}")
    try:
        print(f"median:        {statistics.median(scores):.1f}")
    except statistics.StatisticsError:
        pass
    print("\nNo ATS labels in this corpus—use for smoke / distribution checks vs code changes.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
