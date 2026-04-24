"""Deterministic coaching text generated entirely in Python (no remote LLM)."""

from __future__ import annotations

from typing import Any


def build_python_coach(context: dict[str, Any]) -> dict[str, str]:
    """
    Turn structured scoring context into an actionable narrative.
    This is intentionally template-driven so results are reproducible and auditable.
    """
    overall = context.get("overall_score")
    subs = context.get("subscores") or {}
    plan = context.get("improvement_plan") or []
    missing = context.get("missing_keywords") or []
    weakest = context.get("weakest_segments") or []
    title = context.get("position_title") or ""

    lines: list[str] = []
    lines.append(f"Target role: {title}".strip())
    lines.append(f"Overall score: {overall}/100 (higher is better for this rubric).")
    lines.append("")
    lines.append("Subscore readout:")
    lines.append(
        f"- Format & structure: {subs.get('format_and_structure')}/100 "
        f"(headings, scanability, skills grouping, project layout)."
    )
    lines.append(
        f"- Semantic fit vs JD: {subs.get('semantic_fit_vs_job_description')}/100 "
        f"(embeddings + lexical channels)."
    )
    lines.append(
        f"- Keyword / retrieval fit: {subs.get('keyword_coverage_vs_job_description')}/100 "
        f"(exact important-token overlap + BM25 sentence relevance)."
    )
    lines.append("")
    lines.append("Highest-impact issues (from deterministic rules):")
    if not plan:
        lines.append("- No major structural issues detected by the rubric.")
    else:
        for i, item in enumerate(plan, start=1):
            area = item.get("area", "area")
            why = item.get("why", "")
            fix = item.get("fix", "")
            lines.append(f"{i}) [{area}] {why}")
            lines.append(f"   Action: {fix}")

    if missing:
        lines.append("")
        lines.append("JD terms that did not show up verbatim in the resume (good candidates to mirror if truthful):")
        lines.append(", ".join(missing[:28]))

    if weakest:
        lines.append("")
        lines.append("Resume segments that looked least aligned to the JD under embeddings (rewrite these first):")
        for w in weakest[:3]:
            lines.append(f"- cosine≈{w.get('cosine')} @ offset {w.get('offset')}")

    lines.append("")
    lines.append(
        "Next step: update 2–4 bullets where you honestly have the experience, using the missing terms above, "
        "then re-run scoring."
    )

    return {
        "provider": "python",
        "model": "rss-coach-deterministic-v1",
        "text": "\n".join(lines).strip(),
    }
