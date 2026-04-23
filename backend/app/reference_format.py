"""
Format scoring aligned to the bundled reference resume
(data/reference_resume.docx): name + email, Education (degree/GPA/Batch),
Relevant Coursework, Technical Skills as labeled rows (Category: items),
Projects with "Title | stack" lines plus impact bullets, Soft Skills, Activities.
"""

from __future__ import annotations

import re

from app.paths import DATA_DIR

REFERENCE_FILE = DATA_DIR / "reference_resume.docx"
REFERENCE_LABEL = (
    "Bundled sample layout: Education → Coursework → Technical Skills → "
    "Projects (pipe titles + bullets) → Soft Skills → Activities"
)

SECTION_SPECS: list[tuple[str, str]] = [
    ("education", r"^education\b"),
    ("relevant_coursework", r"^(relevant\s+coursework|coursework|key\s+courses|academic\s+background)\b"),
    ("technical_skills", r"^(technical\s+skills|tech\s*stack|core\s+technologies|(core\s+)?skills)\b"),
    ("work_experience", r"^(work\s+)?experience\b|^(professional\s+)?experience\b|^employment(\s+history)?\b"),
    ("projects", r"^projects\b|^project\s+experience\b|^selected\s+projects\b"),
    ("soft_skills", r"^(soft\s+skills|interpersonal\s+skills)\b"),
    ("activities", r"^(activities|extracurriculars?|leadership\s*&\s*activities)\b"),
]

SKILL_CATEGORY_LINE = re.compile(
    r"^(?!https?:)([A-Z][A-Za-z0-9\s/&+.-]{1,42}):\s+\S",
    re.MULTILINE,
)

PROJECT_TITLE_LINE = re.compile(r"^[^@\n]{3,120}\|[^@\n]{4,}$")

DEGREE_OR_INSTITUTION = re.compile(
    r"\b(university|college|institute|b\.?tech|bachelor|master|"
    r"m\.?tech|ph\.?d|b\.?e\.?|m\.?e\.?|b\.?s\.?|m\.?s\.?)\b",
    re.IGNORECASE,
)
EDU_MARKERS = re.compile(r"\b(gpa|cgpa|batch|class\s+of|expected\s+graduation)\b", re.IGNORECASE)

EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")
NAMEISH_FIRST_LINE = re.compile(
    r"^[A-Za-z][A-Za-z'.-]*(\s+[A-Za-z][A-Za-z'.-]*){0,4}\s*$",
)


def _non_empty_lines(text: str) -> list[str]:
    return [ln.strip() for ln in text.splitlines() if ln.strip()]


def _line_matches_header(line: str, pattern: str) -> bool:
    return bool(re.match(pattern, line.strip(), re.IGNORECASE))


def _section_line_indices(lines: list[str]) -> dict[str, int]:
    found: dict[str, int] = {}
    for i, line in enumerate(lines):
        for key, pat in SECTION_SPECS:
            if key in found:
                continue
            if _line_matches_header(line, pat):
                found[key] = i
                break
    return found


def _word_count(text: str) -> int:
    return len(re.findall(r"[a-zA-Z0-9]+", text))


def _education_block_score(lines: list[str], sections: dict[str, int]) -> tuple[float, dict]:
    if "education" not in sections:
        return 0.0, {"note": "no_education_header"}

    start = sections["education"] + 1
    end_candidates = [
        sections[k]
        for k in ("relevant_coursework", "technical_skills", "work_experience", "projects")
        if k in sections
    ]
    end = min(end_candidates) if end_candidates else min(len(lines), start + 14)
    if end <= start:
        return 0.0, {"note": "education_section_empty"}

    chunk = "\n".join(lines[start:end])
    score = 0.0
    if DEGREE_OR_INSTITUTION.search(chunk):
        score += 8.0
    else:
        score += 3.0
    if EDU_MARKERS.search(chunk):
        score += 7.0
    else:
        score += 2.5
    return min(15.0, score), {"education_span_lines": end - start}


def _skill_category_score(text: str) -> tuple[float, dict]:
    labels = [m.group(1).strip() for m in SKILL_CATEGORY_LINE.finditer(text)]
    n = len(labels)
    ratio = min(1.0, n / 5.0)
    return round(15.0 * ratio, 1), {"skill_category_lines": n, "sample_labels": labels[:8]}


def _project_block_score(lines: list[str], sections: dict[str, int]) -> tuple[float, dict]:
    title_indices = [i for i, ln in enumerate(lines) if PROJECT_TITLE_LINE.match(ln)]
    detail: dict[str, object] = {"project_title_lines": len(title_indices)}

    if not title_indices:
        if "projects" not in sections:
            return 0.0, {**detail, "note": "no_pipe_style_project_titles_or_projects_header"}
        p0 = sections["projects"] + 1
        tail = lines[p0 : p0 + 28]
        long_lines = [ln for ln in tail if len(ln) > 48]
        score = min(12.0, len(long_lines) * 2.8)
        return round(score, 1), {**detail, "fallback_long_lines": len(long_lines)}

    ok_blocks = 0
    for j, idx in enumerate(title_indices):
        next_idx = title_indices[j + 1] if j + 1 < len(title_indices) else min(len(lines), idx + 10)
        body = lines[idx + 1 : next_idx]
        substantial = sum(1 for ln in body if len(ln) > 28)
        if substantial >= 2:
            ok_blocks += 1
        elif substantial == 1:
            ok_blocks += 0.55

    ratio = min(1.0, ok_blocks / 2.0) if title_indices else 0.0
    title_bonus = min(1.0, len(title_indices) / 2.0)
    score = 15.0 * (0.50 * ratio + 0.50 * title_bonus)
    detail["project_blocks_with_2plus_bullets"] = ok_blocks
    return round(min(15.0, score), 1), detail


def _section_order_score(sections: dict[str, int]) -> tuple[float, dict]:
    checks: list[tuple[str, str]] = [
        ("education", "projects"),
        ("technical_skills", "projects"),
        ("work_experience", "projects"),
        ("projects", "soft_skills"),
        ("projects", "activities"),
        ("soft_skills", "activities"),
    ]
    passed = 0
    for a, b in checks:
        if a in sections and b in sections and sections[a] < sections[b]:
            passed += 1
    if "relevant_coursework" in sections and "projects" in sections:
        if sections["relevant_coursework"] < sections["projects"]:
            passed += 1
    total_checks = 7
    score = 5.0 * (passed / total_checks)
    return round(score, 1), {"ordering_checks_passed": passed, "ordering_checks_total": total_checks}


def _lead_name_and_email(lines: list[str]) -> tuple[float, dict]:
    name_ok = bool(lines and NAMEISH_FIRST_LINE.match(lines[0]) and "@" not in lines[0])
    head20 = "\n".join(lines[:20])
    email_ok = bool(EMAIL_RE.search(head20))
    name_pts = 7.5 if name_ok else 4.0
    email_pts = 7.5 if email_ok else 0.0
    return round(min(15.0, name_pts + email_pts), 1), {"name_line_like_reference": name_ok, "email_near_top": email_ok}


def _length_score(wc: int) -> tuple[float, dict]:
    # Slightly wider “good length” band so non-student resumes are not punished.
    if 130 <= wc <= 480:
        s = 5.0
    elif 90 <= wc <= 620:
        s = 3.6
    elif wc < 90:
        s = max(0.0, wc / 90.0 * 3.2)
    else:
        s = max(2.2, 5.0 - min(2.8, (wc - 620) / 450.0))
    return round(s, 1), {"reference_band_words": "≈130–480 words ideal; wider tolerance outside"}


def score_format_against_reference(text: str) -> tuple[float, dict]:
    """Format / layout score 0–100 compared to the bundled reference resume."""
    raw = text.strip()
    if not raw:
        return 0.0, {"error": "empty_document"}

    lines = _non_empty_lines(raw)
    wc = _word_count(raw)
    sections = _section_line_indices(lines)

    section_keys = [k for k, _ in SECTION_SPECS]
    section_match_count = sum(1 for k in section_keys if k in sections)
    section_score = (30.0 / len(section_keys)) * section_match_count

    lead, lead_detail = _lead_name_and_email(lines)
    edu, edu_detail = _education_block_score(lines, sections)
    skills, skills_detail = _skill_category_score(raw)
    proj, proj_detail = _project_block_score(lines, sections)
    order, order_detail = _section_order_score(sections)
    length, length_detail = _length_score(wc)

    total = min(
        100.0,
        section_score + lead + edu + skills + proj + order + length,
    )
    breakdown = {
        "word_count": wc,
        "reference_resume_bundled": REFERENCE_FILE.name,
        "reference_template_description": REFERENCE_LABEL,
        "reference_file_present": REFERENCE_FILE.is_file(),
        "sections_found": {k: sections[k] for k in section_keys if k in sections},
        "section_coverage_score": round(section_score, 1),
        "lead_name_and_email_score": lead,
        "lead_detail": lead_detail,
        "education_block_score": edu,
        "education_detail": edu_detail,
        "technical_skills_rows_score": skills,
        "technical_skills_detail": skills_detail,
        "projects_layout_score": proj,
        "projects_detail": proj_detail,
        "section_order_score": order,
        "section_order_detail": order_detail,
        "length_vs_reference_score": length,
        "length_detail": length_detail,
    }
    return round(total, 1), breakdown


def format_feedback_hints(detail: dict) -> list[str]:
    hints: list[str] = []
    if not detail.get("lead_detail", {}).get("email_near_top"):
        hints.append("Place a professional email near the top (under your name).")
    if not detail.get("lead_detail", {}).get("name_line_like_reference"):
        hints.append("Start with your full name as the first line.")
    sec_found = detail.get("sections_found") or {}
    expected = [k for k, _ in SECTION_SPECS]
    missing = [k for k in expected if k not in sec_found]
    if missing:
        hints.append(
            "Add clear section headings (easy to scan): "
            + ", ".join(k.replace("_", " ") for k in missing[:4])
            + ("…" if len(missing) > 4 else "")
            + "."
        )
    if (detail.get("technical_skills_detail") or {}).get("skill_category_lines", 0) < 3:
        hints.append(
            "Under Technical Skills, use labeled rows (e.g. Languages:, Frontend:, Backend:) for quick scanning."
        )
    if (detail.get("projects_detail") or {}).get("project_title_lines", 0) < 1:
        hints.append(
            "For projects, use a title line with a pipe separating name and stack (e.g. App Name | React, Node) "
            "followed by 2–3 impact bullets."
        )
    return hints
