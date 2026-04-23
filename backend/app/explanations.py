"""Structured 'why' explanations + optional OpenAI-compatible LLM coach."""

from __future__ import annotations

import json
from typing import Any

import httpx

from app.config import Settings


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
                "why": (
                    "One section of the resume reads less aligned to the job description than the rest. "
                    f"Preview: {w0.get('preview')}"
                ),
                "fix": "Rewrite that section with responsibilities and outcomes that mirror the JD’s language and scope.",
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


COACH_SYSTEM = """You are an expert technical resume coach.
You MUST be concrete and non-hallucinatory: only reference facts present in the JSON context.
Output 6-10 short bullet points: what to improve, why it likely lowered scores, and a specific rewrite suggestion.
No flattery. No legal/medical claims."""


async def openai_coach_explanation(
    *,
    settings: Settings,
    context: dict[str, Any],
) -> dict[str, Any] | None:
    """Optional OpenAI-compatible chat completion (remote). Off by default; backend remains Python-only."""
    if not settings.llm_enabled:
        return None

    payload = {
        "model": settings.openai_model,
        "temperature": 0.35,
        "max_tokens": settings.llm_max_tokens,
        "messages": [
            {"role": "system", "content": COACH_SYSTEM},
            {
                "role": "user",
                "content": "Context JSON:\n" + json.dumps(context, ensure_ascii=False)[:18_000],
            },
        ],
    }

    url = f"{settings.openai_base_url}/chat/completions"
    headers = {
        "Authorization": f"Bearer {settings.openai_api_key}",
        "Content-Type": "application/json",
    }
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            r = await client.post(url, headers=headers, json=payload)
            r.raise_for_status()
            data = r.json()
        text = data["choices"][0]["message"]["content"]
        return {"provider": "openai_compatible", "model": settings.openai_model, "text": text.strip()}
    except Exception as exc:  # noqa: BLE001
        return {"provider": "openai_compatible", "model": settings.openai_model, "error": str(exc)[:500]}
