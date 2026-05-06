from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from app.modules.soakaway.calculations import calculate
from app.modules.soakaway.plotting import plot_svg
from app.export.html_render import render_html
from app.export.pdf_export import html_to_pdf


ROOT = Path(__file__).resolve().parents[3]


def _safe_name(value: str) -> str:
    return "".join(
        c if c.isalnum() or c in "-_" else "_"
        for c in str(value)
    )


def _ns(**kwargs):
    return SimpleNamespace(**kwargs)


def _build_canvas(report, plot_path: Path):
    readings = [
        {
            "time_min": row.get("time_min", ""),
            "depth_mbgl": row.get("depth_mbgl", ""),
        }
        for row in report.readings[:36]
    ]

    strata = []
    for row in report.strata:
        strata.append({
            "from_m": row.get("from", row.get("from_m", "")),
            "to_m": row.get("to", row.get("to_m", "")),
            "description": row.get("description", row.get("strata", "")),
        })

    return _ns(
        readings=readings,
        strata=strata,
        plot_image=plot_path.resolve().as_uri(),
        plot_note="",
    )


def _prepare_report_for_master(report, plot_path: Path):
    report.footer_title = "SOAKAWAY BRE 365 TEST"
    report.canvas_template = "templates/soakaway/main_canvas.html"

    logo = ROOT / "assets" / "img" / "igne_logo.png"
    report.logo_path = logo.resolve().as_uri() if logo.exists() else ""

    report.canvas = _build_canvas(report, plot_path)

    return report


def export_pdf(report, output_dir):
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    calculate(report)

    project_id = _safe_name(report.project.get("project_id") or "project")
    loc = _safe_name(report.test.get("location_id") or "location")
    run = _safe_name(report.test.get("test_run") or "1")

    base = f"{project_id}_soakaway_{loc}_run{run}"

    plot_path = output_dir / f"{base}_plot.svg"
    html_path = output_dir / f"{base}.html"
    pdf_path = output_dir / f"{base}.pdf"

    plot_svg(report, plot_path)

    report = _prepare_report_for_master(report, plot_path)

    render_html(
        ROOT / "templates" / "shared" / "base_report.html",
        {"report": report},
        html_path,
    )

    html_to_pdf(html_path, pdf_path)

    return pdf_path
