"""What we persist from a scoring run (privacy / deploy defaults)."""

from __future__ import annotations

from typing import Any


def _sanitize_improvement_plan_for_db(plan: Any) -> Any:
    if not isinstance(plan, list):
        return plan
    out: list[dict[str, Any]] = []
    for item in plan:
        if not isinstance(item, dict):
            continue
        d = dict(item)
        d.pop("snippet_image_base64", None)
        d.pop("snippet_image_mime", None)
        d.pop("snippet_image_url", None)
        d.pop("snippet_full_document_preview", None)
        sn = d.get("snippet")
        if isinstance(sn, dict):
            sn2 = dict(sn)
            sn2.pop("text_preview", None)
            d["snippet"] = sn2
        out.append(d)
    return out


def scoring_run_payload_for_db(result: dict[str, Any], *, store_sensitive: bool) -> dict[str, Any]:
    """
    When `store_sensitive` is False, omit resume/JD-derived blobs from the DB row
    (API response to the client is still the full `result` dict in memory).
    """
    if store_sensitive:
        return dict(result)

    gap = result.get("gap_report") or {}
    return {
        "overall_score": result.get("overall_score"),
        "subscores": result.get("subscores"),
        "weights_applied": result.get("weights_applied"),
        "position_title_considered": result.get("position_title_considered"),
        "improvement_plan": _sanitize_improvement_plan_for_db(result.get("improvement_plan")),
        "feedback": result.get("feedback"),
        # Ephemeral UI helpers; don't persist tokens/URLs.
        "weak_section_snippet": None,
        "annotated_document_preview": None,
        "gap_report": {
            "missing_keywords_from_jd": gap.get("missing_keywords_from_jd"),
            "keyword_stats": gap.get("keyword_stats"),
            "format_highlights": gap.get("format_highlights"),
        },
    }
