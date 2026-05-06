from __future__ import annotations

from pathlib import Path
from copy import deepcopy
from types import SimpleNamespace

from app.export.html_render import render_html
from app.export.pdf_export import html_to_pdf
from app.core.pdf_merge import merge_pdfs
from app.modules.borehole.layout import build_strip_layout
from app.modules.borehole.paginate import borehole_pages
from app.modules.borehole.svg_log import render_borehole_svg


ROOT = Path(__file__).resolve().parents[3]


def _safe_name(value: str) -> str:
    return "".join(c if c.isalnum() or c in "-_" else "_" for c in str(value))


def _ns(**kwargs):
    return SimpleNamespace(**kwargs)


def _prepare_report(report, svg_path: Path, page_no: int, total_pages: int, depth_from: float, depth_to: float):
    r = deepcopy(report)

    logo = ROOT / "assets" / "img" / "igne_logo.png"
    r.logo_path = logo.resolve().as_uri() if logo.exists() else ""

    r.footer_title = "BOREHOLE LOG"
    r.canvas_template = "templates/borehole/main_canvas.html"

    r.page.current = str(page_no)
    r.page.total = str(total_pages)

    r.test.test_run = f"{depth_from:g}–{depth_to:g} m"

    r.canvas = _ns(
        log_svg=svg_path.resolve().as_uri(),
    )

    return r


def export_pdf(
    report,
    output_dir,
    strip_layout_rows: list[dict],
    dcp_tests: list[dict] | None = None,
    soakaway_reports: list | None = None,
):
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    project_id = _safe_name(report.project.project_id or "project")
    loc = _safe_name(report.test.location_id or "location")

    pages = borehole_pages(report)
    strips = build_strip_layout(strip_layout_rows)

    page_pdfs = []

    for page in pages:
        base = f"{project_id}_borehole_{loc}_p{page['page_no']:02d}"

        svg_path = output_dir / f"{base}_log.svg"
        html_path = output_dir / f"{base}.html"
        pdf_path = output_dir / f"{base}.pdf"

        render_borehole_svg(
            report=report,
            page=page,
            strips=strips,
            output_path=svg_path,
            dcp_tests=dcp_tests,
            soakaway_reports=soakaway_reports,
        )

        page_report = _prepare_report(
            report,
            svg_path,
            page["page_no"],
            page["total_pages"],
            page["depth_from"],
            page["depth_to"],
        )

        render_html(
            ROOT / "templates" / "shared" / "base_report.html",
            {"report": page_report},
            html_path,
        )

        html_to_pdf(html_path, pdf_path)
        page_pdfs.append(pdf_path)

    merged = output_dir / f"{project_id}_borehole_{loc}.pdf"
    merge_pdfs(page_pdfs, merged)

    return merged
