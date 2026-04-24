"""Structured 'why' explanations for scoring (Python-only; no remote LLM)."""

from __future__ import annotations

from typing import Any


def build_improvement_plan(
    *,
    overall: float,
    fmt: float,
    sem: float,
    kw: float,
    gap_report: dict[str, Any],
    format_hints: list[str],
) -> list[dict[str, Any]]:
    """Deterministic, auditable reasons tied to measurable signals."""
    plan: list[dict[str, Any]] = []

    missing = gap_report.get("missing_keywords_from_jd") or []
    if kw < 62 and missing:
        top = ", ".join(missing[:12])
        plan.append(
            {
                "area": "keyword_coverage_vs_job_description",
                "severity": "high" if kw < 48 else "medium",
                "why": f"Many substantive job-description terms do not appear verbatim in the resume (examples: {top}).",
                "fix": "Where accurate, weave JD vocabulary into your bullets (tools, methods, outcomes)—especially missing terms above.",
            }
        )

    weak = gap_report.get("weakest_resume_segments_vs_jd") or []
    if sem < 62 and weak:
        w0 = weak[0]
        plan.append(
            {
                "area": "semantic_fit_vs_job_description",
                "severity": "high" if sem < 48 else "medium",
                "why": "One section of the resume reads less aligned to the job description than the rest.",
                "fix": "Rewrite that section with responsibilities and outcomes that mirror the JD’s language and scope.",
                # UI can render a PDF band image if the original upload was a PDF (see scoring_service).
                "snippet": {
                    "kind": "resume_pdf_band",
                    "offset": w0.get("offset"),
                    "cosine": w0.get("cosine"),
                    "text_preview": w0.get("preview"),
                },
            }
        )

    if fmt < 76:
        hints = "; ".join(format_hints[:3]) if format_hints else "Improve sectioning and scanability."
        plan.append(
            {
                "area": "format_and_structure",
                "severity": "medium" if fmt >= 58 else "high",
                "why": "The resume is harder to scan (sections/headings/structure) than strong performers for this rubric.",
                "fix": hints,
            }
        )

    if overall >= 72 and not plan:
        plan.append(
            {
                "area": "overall",
                "severity": "low",
                "why": "Scores are already strong relative to this rubric.",
                "fix": "Tighten wording, quantify impact, and tailor a few bullets to the exact team/product.",
            }
        )

    return plan[:8]

