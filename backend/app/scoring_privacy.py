"""What we persist from a scoring run (privacy / deploy defaults)."""

from __future__ import annotations

from typing import Any


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
        "improvement_plan": result.get("improvement_plan"),
        "feedback": result.get("feedback"),
        "gap_report": {
            "missing_keywords_from_jd": gap.get("missing_keywords_from_jd"),
            "keyword_stats": gap.get("keyword_stats"),
            "format_highlights": gap.get("format_highlights"),
        },
    }
