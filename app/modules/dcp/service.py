from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from statistics import mean

from app.export.html_render import render_html
from app.export.pdf_export import html_to_pdf
from app.modules.dcp.plotting import plot_svg
from app.modules.dcp.layers import calculate_layer_icbr


ROOT = Path(__file__).resolve().parents[3]


def _safe_name(value: str) -> str:
    return "".join(c if c.isalnum() or c in "-_" else "_" for c in str(value))


def _ns(**kwargs):
    return SimpleNamespace(**kwargs)


def _to_float(v):
    try:
        if v is None or v == "":
            return None
        return float(v)
    except Exception:
        return None


def _fmt(v, ndp=3):
    if v is None:
        return ""
    s = f"{v:.{ndp}f}"
    return s.rstrip("0").rstrip(".")


def _field(*values):
    for v in values:
        if v not in (None, ""):
            return v
    return ""


def _build_readings(dcp_test):
    rows = []

    for row in dcp_test.get("data", [])[:36]:
        rows.append({
            "depth_m": _fmt(_to_float(row.get("DCPT_DPTH")), 3),
            "blows": row.get("DCPT_BLOW", ""),
            "icbr": _fmt(_to_float(row.get("DCPT_ICBR_EST")), 2),
        })

    return rows


def _calc_stats(dcp_test):
    rows = dcp_test.get("data", []) or []

    depths = [_to_float(r.get("DCPT_DPTH")) for r in rows]
    icbrs = [_to_float(r.get("DCPT_ICBR_EST")) for r in rows]

    depths = [d for d in depths if d is not None]
    icbrs = [i for i in icbrs if i is not None]

    max_depth = max(depths) if depths else None
    min_icbr = min(icbrs) if icbrs else None
    avg_icbr = mean(icbrs) if icbrs else None
    max_icbr = max(icbrs) if icbrs else None

    return {
        "max_depth": _fmt(max_depth, 2),
        "min_icbr": _fmt(min_icbr, 2),
        "avg_icbr": _fmt(avg_icbr, 2),
        "max_icbr": _fmt(max_icbr, 2),
    }


def _prepare_report(dcp_test, plot_path: Path, layers: list[dict] | None = None):
    general = dcp_test.get("general", {}) or {}
    loca = dcp_test.get("loca", {}) or {}

    stats = _calc_stats(dcp_test)

    layer_summary = calculate_layer_icbr(dcp_test, layers or [])

    rep_values = [
        _to_float(row.get("representative_icbr"))
        for row in layer_summary
    ]
    rep_values = [v for v in rep_values if v is not None]
    rep_icbr = min(rep_values) if rep_values else None

    logo = ROOT / "assets" / "img" / "igne_logo.png"

    report = _ns(
        project=_ns(
            project_name=_field(general.get("PROJ_NAME"), loca.get("PROJ_NAME"), ""),
            client=_field(general.get("CLIENT"), loca.get("CLIENT"), general.get("CLNT_NAME"), ""),
            project_engineer=_field(general.get("PROJECT_ENGINEER"), loca.get("PROJECT_ENGINEER"), general.get("PROJ_ENG"), ""),
            project_id=_field(dcp_test.get("project_id"), general.get("PROJ_ID"), loca.get("PROJ_ID"), ""),
        ),
        test=_ns(
            location_id=_field(dcp_test.get("location_id"), general.get("LOCA_ID"), loca.get("LOCA_ID"), ""),
            test_run=_field(general.get("DCPG_RUN"), "1"),
            test_date=_field(general.get("DCPG_DATE"), general.get("DATE"), ""),
            tested_by=_field(general.get("DCPG_TESTED_BY"), general.get("TESTED_BY"), ""),
        ),
        location=_ns(
            easting=_field(loca.get("LOCA_NATE"), loca.get("EASTING"), ""),
            northing=_field(loca.get("LOCA_NATN"), loca.get("NORTHING"), ""),
            ground_level=_field(loca.get("LOCA_GL"), loca.get("GROUND_LEVEL"), ""),
        ),
        subfooter=_ns(
            remarks="Derived from DCPG/DCPT data.",
            instrument="Dynamic Cone Penetrometer",
            methodology="ICBR estimated from DCPT data",
        ),
        signoff=_ns(
            originator="TK",
            status="Prelim",
            checked_approved="",
            issue_date="",
        ),
        page=_ns(
            fig_no="",
            current="1",
            total="1",
        ),
        footer_title="DCP / ICBR TEST",
        canvas_template="templates/dcp/main_canvas.html",
        logo_path=logo.resolve().as_uri() if logo.exists() else "",
        canvas=_ns(
            readings=_build_readings(dcp_test),
            row_count=len(dcp_test.get("data", []) or []),
            max_depth=stats["max_depth"],
            min_icbr=stats["min_icbr"],
            avg_icbr=stats["avg_icbr"],
            max_icbr=stats["max_icbr"],
            rep_icbr=_fmt(rep_icbr, 2),
            summary_rows=[
                {
                    "from_m": row.get("from_m", ""),
                    "to_m": row.get("to_m", ""),
                    "icbr": row.get("representative_icbr", ""),
                }
                for row in layer_summary[:6]
            ],
            plot_image=plot_path.resolve().as_uri(),
            plot_note="",
        ),
    )

    return report


def export_pdf(dcp_test, output_dir, layers: list[dict] | None = None):
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    project_id = _safe_name(dcp_test.get("project_id") or "project")
    loc = _safe_name(dcp_test.get("location_id") or "location")

    base = f"{project_id}_dcp_{loc}"

    plot_path = output_dir / f"{base}_plot.svg"
    html_path = output_dir / f"{base}.html"
    pdf_path = output_dir / f"{base}.pdf"

    plot_svg(dcp_test, plot_path)

    report = _prepare_report(dcp_test, plot_path, layers)

    render_html(
        ROOT / "templates" / "shared" / "base_report.html",
        {"report": report},
        html_path,
    )

    html_to_pdf(html_path, pdf_path)

    return pdf_path
