#!/usr/bin/env python3
"""
Benchmark RSS scoring against Hugging Face `0xnbk/resume-ats-score-v1-en`.

The dataset has resume `text` and label `ats_score` only (no job description per row).
We score every row against a fixed generic JD so the existing pipeline runs, then
report MAE and Pearson correlation between our overall_score and ats_score.

Usage:
  cd backend && ../.venv/bin/python benchmark_hf_resume_ats.py --split validation --limit 200
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np

BACKEND_ROOT = Path(__file__).resolve().parent
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.benchmark_common import GENERIC_JD, GENERIC_TITLE  # noqa: E402
from app.dataset_hf import load_resume_ats_split, resolve_resume_ats_repo_id  # noqa: E402
from app.scoring import score_resume  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser(description="Benchmark RSS vs HF resume–ATS scores.")
    ap.add_argument("--repo", default=None, help="HF dataset id (default: 0xnbk/resume-ats-score-v1-en)")
    ap.add_argument("--split", default="validation", choices=["train", "validation"])
    ap.add_argument("--limit", type=int, default=200, help="Max rows (0 = all)")
    ap.add_argument("--offset", type=int, default=0, help="Skip first N rows after load")
    args = ap.parse_args()

    rid = resolve_resume_ats_repo_id(args.repo)
    max_rows = None if args.limit == 0 else args.limit + max(0, args.offset)
    ds = load_resume_ats_split(args.repo, split=args.split, max_rows=max_rows)
    if args.offset > 0:
        ds = ds.select(range(args.offset, len(ds)))

    y_true: list[float] = []
    y_pred: list[float] = []

    print(f"Dataset: {rid}  split={args.split}  rows={len(ds)}", flush=True)

    for i, row in enumerate(ds):
        text = (row.get("text") or "").strip()
        if len(text) < 80:
            continue
        ats = float(row["ats_score"])
        out = score_resume(text, GENERIC_JD, GENERIC_TITLE)
        pred = float(out["overall_score"])
        y_true.append(ats)
        y_pred.append(pred)
        if (i + 1) % 50 == 0:
            print(f"  scored {i + 1}/{len(ds)}", flush=True)

    if len(y_true) < 2:
        print(
            "Too few valid rows after filtering (need text length >= 80 per row). "
            "Try --limit 20 or a different --split.",
            file=sys.stderr,
        )
        return 1

    a = np.asarray(y_true, dtype=np.float64)
    b = np.asarray(y_pred, dtype=np.float64)
    mae = float(np.mean(np.abs(a - b)))
    if len(y_true) >= 3 and np.std(a) > 1e-9 and np.std(b) > 1e-9:
        r = float(np.corrcoef(a, b)[0, 1])
    else:
        r = float("nan")

    print("\n--- Results (generic JD; interpret loosely) ---")
    print(f"n_samples:     {len(y_true)}")
    print(f"MAE:           {mae:.3f}   (mean |ours - ats_score|)")
    print(f"Pearson r:     {r:.4f}   (ours vs ats_score)")
    print("\nNote: labels are ATS-style resume scores without a specific posting; our scorer is JD-aware,")
    print("so this benchmark is mainly for regression tracking, not absolute accuracy claims.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
