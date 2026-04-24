"""Render a small vertical band \"snippet\" as a PNG (best-effort).

Supports:
- PDF: render first page via pdfium and crop a horizontal band
- Images: crop a band from the image
- Office docs: if LibreOffice `soffice` is installed, convert to PDF then render/crop
- PDF (and Office→PDF): full stacked pages with approximate highlight bands for weak JD-alignment chunks
"""

from __future__ import annotations

from io import BytesIO
from pathlib import Path
from shutil import which
import subprocess
import tempfile
from typing import Any


def render_text_highlight_preview_png(
    *,
    resume_text: str,
    weak_segments: list[dict[str, Any]] | None,
    max_items: int = 4,
) -> bytes:
    """Always-available preview: render extracted text + weak chunk previews into a PNG."""
    from PIL import Image, ImageDraw, ImageFont

    resume = (resume_text or "").strip()
    segs = [s for s in (weak_segments or []) if isinstance(s, dict)][:max_items]
    w = 960
    h = 1180
    pad = 34
    bg = (255, 255, 255)
    canvas = Image.new("RGB", (w, h), bg)
    draw = ImageDraw.Draw(canvas)

    try:
        font_title = ImageFont.truetype("Arial.ttf", 22)
        font_body = ImageFont.truetype("Arial.ttf", 14)
        font_mono = ImageFont.truetype("Courier New.ttf", 13)
    except Exception:  # noqa: BLE001
        font_title = ImageFont.load_default()
        font_body = ImageFont.load_default()
        font_mono = ImageFont.load_default()

    y = pad
    draw.text((pad, y), "Extracted text preview (highlights)", fill=(20, 24, 32), font=font_title)
    y += 34
    draw.text(
        (pad, y),
        "File rendering failed or was unsupported. This fallback preview is generated from extracted text.",
        fill=(85, 95, 110),
        font=font_body,
    )
    y += 28

    def _wrap(s: str, max_chars: int) -> list[str]:
        s2 = " ".join((s or "").split())
        if not s2:
            return ["—"]
        out: list[str] = []
        while s2:
            out.append(s2[:max_chars])
            s2 = s2[max_chars:]
        return out

    # Show a short slice of extracted text.
    excerpt = resume[:1600] + ("…" if len(resume) > 1600 else "")
    box_h = 280
    draw.rounded_rectangle([pad, y, w - pad, y + box_h], radius=18, outline=(220, 225, 235), width=2, fill=(248, 250, 252))
    y2 = y + 16
    for line in _wrap(excerpt, 120)[:14]:
        draw.text((pad + 16, y2), line, fill=(35, 42, 55), font=font_mono)
        y2 += 18
    y += box_h + 22

    # Weak chunks list.
    draw.text((pad, y), "Weak alignment chunks (rewrite these first)", fill=(20, 24, 32), font=font_body)
    y += 22
    colors = [(255, 90, 90), (255, 160, 60), (80, 180, 255), (60, 220, 160)]
    for i, seg in enumerate(segs):
        preview = str(seg.get("preview") or seg.get("text_preview") or "").strip()
        if not preview:
            continue
        c = colors[i % len(colors)]
        card_h = 150
        draw.rounded_rectangle([pad, y, w - pad, y + card_h], radius=18, outline=(220, 225, 235), width=2, fill=(255, 255, 255))
        draw.rounded_rectangle([pad + 14, y + 14, pad + 26, y + card_h - 14], radius=6, fill=c)
        y3 = y + 14
        draw.text((pad + 36, y3), f"Chunk {i + 1}", fill=(20, 24, 32), font=font_body)
        y3 += 22
        for line in _wrap(preview, 118)[:6]:
            draw.text((pad + 36, y3), line, fill=(35, 42, 55), font=font_mono)
            y3 += 18
        y += card_h + 14
        if y > h - 180:
            break

    buf = BytesIO()
    canvas.save(buf, format="PNG", optimize=True)
    return buf.getvalue()


def _candidate_soffice_paths() -> list[str]:
    # Common locations (macOS Homebrew cask installs here).
    return [
        "/Applications/LibreOffice.app/Contents/MacOS/soffice",
        "/usr/bin/soffice",
        "/usr/local/bin/soffice",
        "/opt/homebrew/bin/soffice",
    ]


def soffice_path() -> str | None:
    w = which("soffice")
    if w:
        return w
    for p in _candidate_soffice_paths():
        if Path(p).is_file():
            return p
    return None


def render_pdf_vertical_band_png(
    pdf_bytes: bytes,
    *,
    y_center_ratio: float,
    dpi: int = 160,
    band_ratio: float = 0.28,
    page_index: int = 0,
    max_side: int = 1400,
) -> bytes:
    """Return PNG bytes cropped from a PDF page.

    `y_center_ratio` is 0..1 within the page height (top=0). This is intentionally approximate:
    we map resume-text offsets to a vertical band on page 1 for a readable "snippet" preview.
    """
    import pypdfium2 as pdfium  # type: ignore
    from PIL import Image

    pdf = pdfium.PdfDocument(pdf_bytes)
    if len(pdf) < 1:
        raise ValueError("Empty PDF")

    page = pdf[min(max(page_index, 0), len(pdf) - 1)]
    scale = dpi / 72.0
    bmp = page.render(scale=scale).to_pil()
    if not isinstance(bmp, Image.Image):
        bmp = Image.fromarray(bmp)  # pragma: no cover

    w, h = bmp.size
    y_center_ratio = min(0.92, max(0.08, float(y_center_ratio)))
    band_ratio = min(0.55, max(0.12, float(band_ratio)))

    band_h = max(120, int(h * band_ratio))
    cy = int(h * y_center_ratio)
    y0 = max(0, min(h - band_h, cy - band_h // 2))
    crop = bmp.crop((0, y0, w, y0 + band_h))

    cw, ch = crop.size
    m = max(cw, ch)
    if m > max_side:
        s = max_side / m
        crop = crop.resize((max(1, int(cw * s)), max(1, int(ch * s))), Image.Resampling.LANCZOS)

    buf = BytesIO()
    crop.save(buf, format="PNG", optimize=True)
    return buf.getvalue()


def render_image_vertical_band_png(
    image_bytes: bytes,
    *,
    y_center_ratio: float,
    band_ratio: float = 0.28,
    max_side: int = 1400,
) -> bytes:
    from PIL import Image

    img = Image.open(BytesIO(image_bytes))
    img = img.convert("RGB")
    w, h = img.size
    y_center_ratio = min(0.92, max(0.08, float(y_center_ratio)))
    band_ratio = min(0.75, max(0.12, float(band_ratio)))

    band_h = max(120, int(h * band_ratio))
    cy = int(h * y_center_ratio)
    y0 = max(0, min(h - band_h, cy - band_h // 2))
    crop = img.crop((0, y0, w, y0 + band_h))

    cw, ch = crop.size
    m = max(cw, ch)
    if m > max_side:
        s = max_side / m
        crop = crop.resize((max(1, int(cw * s)), max(1, int(ch * s))), Image.Resampling.LANCZOS)

    buf = BytesIO()
    crop.save(buf, format="PNG", optimize=True)
    return buf.getvalue()


def _soffice_available() -> bool:
    return soffice_path() is not None


def _convert_office_to_pdf_bytes(filename: str, data: bytes) -> bytes:
    """Convert office bytes (docx/pptx/xlsx) to PDF bytes using LibreOffice if available."""
    soffice = soffice_path()
    if not soffice:
        raise RuntimeError("LibreOffice (soffice) not installed; cannot render this file type as an image.")

    ext = Path(filename).suffix.lower() or ".bin"
    with tempfile.TemporaryDirectory(prefix="rss-snippet-") as td:
        tmpdir = Path(td)
        src = tmpdir / f"input{ext}"
        src.write_bytes(data)
        # Convert to PDF.
        # LibreOffice writes output with the same basename.
        subprocess.run(
            [soffice, "--headless", "--nologo", "--nolockcheck", "--nodefault", "--nofirststartwizard",
             "--convert-to", "pdf", "--outdir", str(tmpdir), str(src)],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        out = tmpdir / (src.stem + ".pdf")
        if not out.is_file():
            # Sometimes LO produces uppercase extension.
            alt = tmpdir / (src.stem + ".PDF")
            if alt.is_file():
                out = alt
            else:
                raise RuntimeError("LibreOffice conversion failed (no PDF produced).")
        return out.read_bytes()


def render_file_snippet_png(
    filename: str,
    data: bytes,
    *,
    y_center_ratio: float,
) -> bytes:
    """Best-effort snippet image for many file types."""
    lower = (filename or "").lower()
    if lower.endswith(".pdf"):
        return render_pdf_vertical_band_png(data, y_center_ratio=y_center_ratio)
    if lower.endswith((".png", ".jpg", ".jpeg", ".webp")):
        return render_image_vertical_band_png(data, y_center_ratio=y_center_ratio)
    if lower.endswith((".docx", ".pptx", ".xlsx")):
        pdf = _convert_office_to_pdf_bytes(filename, data)
        return render_pdf_vertical_band_png(pdf, y_center_ratio=y_center_ratio)

    raise RuntimeError("Unsupported file type for snippet image.")


# Must stay aligned with `gap_analysis.weakest_resume_spans` default chunk_size.
_GAP_EMBED_CHUNK_CHARS = 420


def _pdf_bytes_for_preview(filename: str, data: bytes) -> bytes:
    lower = (filename or "").lower()
    if lower.endswith(".pdf"):
        return data
    if lower.endswith((".docx", ".pptx", ".xlsx")):
        return _convert_office_to_pdf_bytes(filename, data)
    raise RuntimeError("Annotated full-document preview needs PDF or convertible Office upload.")


def _char_span_for_weak_segment(resume: str, w: dict[str, Any]) -> tuple[int, int]:
    n = len(resume)
    if n < 1:
        return 0, 0
    off_raw = w.get("offset", 0)
    try:
        start = int(off_raw) if off_raw is not None else 0
    except Exception:  # noqa: BLE001
        start = 0
    start = max(0, min(max(0, n - 1), start))
    preview = w.get("preview")
    prev_s = str(preview).strip() if preview is not None else ""
    if len(prev_s) >= 24:
        at = resume.find(prev_s)
        if at != -1:
            start = at
    end = min(n, start + _GAP_EMBED_CHUNK_CHARS)
    if end <= start:
        end = min(n, start + 80)
    return start, end


def render_file_annotated_preview_png(
    filename: str,
    data: bytes,
    *,
    resume_text: str,
    weak_segments: list[dict[str, Any]] | None,
) -> bytes:
    """Stack PDF pages (downscaled) and draw semi-transparent bands for weak semantic chunks.

    Band placement uses a linear map from resume character offsets to vertical position in the
    stacked page image (approximation when PDF text order differs from our extracted plain text).
    """
    from PIL import Image, ImageDraw

    lower = (filename or "").lower()
    resume = (resume_text or "").strip()
    n_chars = max(1, len(resume))
    segs = [s for s in (weak_segments or []) if isinstance(s, dict)][:6]

    # Image uploads: treat as a single "page" canvas.
    if lower.endswith((".png", ".jpg", ".jpeg", ".webp")):
        img = Image.open(BytesIO(data)).convert("RGB")
        max_output_width = 960
        if img.width > max_output_width and img.width > 0:
            s = max_output_width / img.width
            img = img.resize((max_output_width, max(1, int(img.height * s))), Image.Resampling.LANCZOS)
        canvas = img
        draw = ImageDraw.Draw(canvas, "RGBA")
        total_h = canvas.height

        # Draw highlight bands using the same linear offset mapping.
        colors = [
            (255, 90, 90, 90),
            (255, 160, 60, 90),
            (255, 220, 60, 90),
            (80, 180, 255, 90),
            (140, 120, 255, 90),
            (60, 220, 160, 90),
        ]
        for i, wseg in enumerate(segs):
            start, end = _char_span_for_weak_segment(resume, wseg)
            y0 = int((start / n_chars) * max(1, total_h - 1))
            y1 = int((end / n_chars) * max(1, total_h - 1))
            y0 = max(0, min(total_h - 1, y0))
            y1 = max(y0 + 10, min(total_h, y1 + 10))
            col = colors[i % len(colors)]
            draw.rectangle([0, y0, canvas.width, y1], fill=col, outline=(0, 0, 0, 45))

        buf = BytesIO()
        canvas.save(buf, format="PNG", optimize=True)
        return buf.getvalue()

    # PDF / Office: stack pages and annotate.
    import pypdfium2 as pdfium  # type: ignore
    pdf_bytes = _pdf_bytes_for_preview(filename, data)

    pdf = pdfium.PdfDocument(pdf_bytes)
    if len(pdf) < 1:
        raise ValueError("Empty PDF")

    dpi = 102
    max_pages = 14
    max_output_width = 960
    gap = 10
    n_pages = min(len(pdf), max_pages)

    page_images: list[Any] = []
    for i in range(n_pages):
        try:
            page = pdf[i]
            scale = dpi / 72.0
            bmp = page.render(scale=scale).to_pil()
            if not isinstance(bmp, Image.Image):
                bmp = Image.fromarray(bmp)  # pragma: no cover
            bmp = bmp.convert("RGB")
            w, h = bmp.size
            if w > max_output_width and w > 0:
                s = max_output_width / w
                bmp = bmp.resize((max_output_width, max(1, int(h * s))), Image.Resampling.LANCZOS)
            page_images.append(bmp)
        except Exception:  # noqa: BLE001
            continue

    if not page_images:
        raise RuntimeError("Could not render any PDF pages for preview.")

    total_w = max(im.width for im in page_images)
    total_h = sum(im.height for im in page_images) + gap * (len(page_images) - 1)
    canvas = Image.new("RGB", (total_w, total_h), (255, 255, 255))
    y0 = 0
    for im in page_images:
        xoff = (total_w - im.width) // 2
        canvas.paste(im, (xoff, y0))
        y0 += im.height + gap

    if segs:
        bands: list[tuple[int, int]] = []
        min_band = max(44, int(canvas.height * 0.04))
        for w in segs:
            lo, hi = _char_span_for_weak_segment(resume, w)
            y_top = int((lo / n_chars) * canvas.height)
            y_bot = int((hi / n_chars) * canvas.height)
            y_bot = max(y_bot, y_top + min_band)
            y_top = max(0, min(canvas.height - 2, y_top))
            y_bot = max(y_top + 2, min(canvas.height, y_bot))
            bands.append((y_top, y_bot))

        overlay = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
        dr = ImageDraw.Draw(overlay)
        colors = [
            (239, 68, 68, 72),
            (245, 158, 11, 72),
            (234, 179, 8, 72),
            (168, 85, 247, 72),
            (59, 130, 246, 72),
            (16, 185, 129, 72),
        ]
        margin = 6
        for idx, (yt, yb) in enumerate(bands):
            fill = colors[idx % len(colors)]
            dr.rectangle(
                [margin, yt, canvas.width - margin - 1, yb - 1],
                fill=fill,
                outline=(fill[0], fill[1], fill[2], 230),
                width=4,
            )
            # small numbered tab
            lab = str(idx + 1)
            tw, th = 22, 22
            lx = margin + 4
            ly = max(0, yt - th // 3)
            dr.rounded_rectangle([lx, ly, lx + tw, ly + th], radius=6, fill=(17, 24, 39, 230))
            dr.text((lx + 7, ly + 4), lab, fill=(255, 255, 255, 255))

        canvas_rgba = canvas.convert("RGBA")
        canvas_rgba = Image.alpha_composite(canvas_rgba, overlay)
        canvas = canvas_rgba.convert("RGB")

    max_stack_h = 26_000
    if canvas.height > max_stack_h:
        s = max_stack_h / canvas.height
        canvas = canvas.resize(
            (max(1, int(canvas.width * s)), max_stack_h),
            Image.Resampling.LANCZOS,
        )

    buf = BytesIO()
    canvas.save(buf, format="PNG", optimize=True)
    return buf.getvalue()
