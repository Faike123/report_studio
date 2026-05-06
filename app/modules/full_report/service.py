from __future__ import annotations

from pathlib import Path
from collections import defaultdict
import html
import math

from app.export.pdf_export import html_to_pdf


ROOT = Path(__file__).resolve().parents[3]


KNOWN_DEPTH_FIELDS = {
    "GEOL": ("GEOL_TOP", "GEOL_BASE"),
    "SAMP": ("SAMP_TOP", "SAMP_BASE"),
    "ISPT": ("ISPT_TOP", None),
    "WSTD": ("WSTD_DPTH", None),
    "WSTG": ("WSTG_DPTH", None),
    "CORE": ("CORE_TOP", "CORE_BASE"),
    "FRAC": ("FRAC_DPTH", None),
    "FRCT": ("FRCT_DPTH", None),
    "DCPG": (None, None),
    "DCPT": ("DCPT_DPTH", None),
    "ICBR": ("ICBR_FROM", "ICBR_TO"),
    "ISAG": (None, None),
    "ISAT": ("ISAT_DPTH", None),
    "IVAN": ("IVAN_DPTH", None),
    "IPID": ("IPID_DPTH", None),
}


GROUP_LABELS = {
    "PROJ": "Project Information",
    "LOCA": "Location Details",
    "GEOL": "Geology Descriptions",
    "SAMP": "Samples",
    "ISPT": "SPT Tests",
    "WSTD": "Groundwater / Water Strikes",
    "WSTG": "Groundwater / Water Strikes",
    "CORE": "Core Recovery",
    "FRAC": "Fractures",
    "FRCT": "Fractures",
    "DCPG": "DCP General",
    "DCPT": "DCP Data",
    "ICBR": "In Situ CBR",
    "ISAG": "Soakaway General",
    "ISAT": "Soakaway Data",
    "IVAN": "Hand Vane",
    "IPID": "PID Results",
}


def _esc(value) -> str:
    return html.escape("" if value is None else str(value))


def _safe(value: str) -> str:
    value = str(value or "").strip()
    return "".join(c if c.isalnum() or c in "-_" else "_" for c in value) or "unknown"


def _f(value, default=None):
    try:
        if value in (None, ""):
            return default
        return float(value)
    except Exception:
        return default


def _group_rows(parsed: dict, group: str) -> list[dict]:
    return parsed.get("groups", {}).get(group, []) or []


def _headings(parsed: dict, group: str) -> list[str]:
    return parsed.get("headings", {}).get(group, []) or []


def _all_groups(parsed: dict) -> list[str]:
    return sorted(parsed.get("groups", {}).keys())


def _project_id(parsed: dict) -> str:
    proj = _group_rows(parsed, "PROJ")
    if proj:
        for key in ("PROJ_ID", "PROJ_NAME"):
            if proj[0].get(key):
                return str(proj[0].get(key))
    loca = _group_rows(parsed, "LOCA")
    if loca and loca[0].get("PROJ_ID"):
        return str(loca[0].get("PROJ_ID"))
    return Path(parsed.get("name", "ags_report")).stem


def _project_name(parsed: dict) -> str:
    proj = _group_rows(parsed, "PROJ")
    if proj:
        return proj[0].get("PROJ_NAME") or proj[0].get("PROJ_DESC") or ""
    loca = _group_rows(parsed, "LOCA")
    if loca:
        return loca[0].get("PROJ_NAME") or loca[0].get("PROJ_DESC") or ""
    return ""


def _locations(parsed: dict) -> list[dict]:
    loca = _group_rows(parsed, "LOCA")
    rows = []

    for row in loca:
        rows.append({
            "LOCA_ID": row.get("LOCA_ID", ""),
            "LOCA_TYPE": row.get("LOCA_TYPE", ""),
            "LOCA_NATE": row.get("LOCA_NATE", row.get("LOCA_LOCX", "")),
            "LOCA_NATN": row.get("LOCA_NATN", row.get("LOCA_LOCY", "")),
            "LOCA_GL": row.get("LOCA_GL", row.get("LOCA_LOCZ", "")),
            "LOCA_FDEP": row.get("LOCA_FDEP", ""),
            "LOCA_METH": row.get("LOCA_METH", ""),
        })

    return rows


def _rows_by_loca(parsed: dict) -> dict[str, dict[str, list[dict]]]:
    out = defaultdict(lambda: defaultdict(list))

    for group, rows in parsed.get("groups", {}).items():
        for row in rows:
            loca_id = str(row.get("LOCA_ID", "")).strip()
            if not loca_id:
                continue
            out[loca_id][group].append(row)

    return out


def _location_max_depth(parsed: dict, loca_id: str) -> float:
    by_loca = _rows_by_loca(parsed)
    groups = by_loca.get(loca_id, {})

    depths = []

    loca_rows = groups.get("LOCA", [])
    for row in loca_rows:
        v = _f(row.get("LOCA_FDEP"))
        if v is not None:
            depths.append(v)

    for group, rows in groups.items():
        top_field, base_field = KNOWN_DEPTH_FIELDS.get(group, (None, None))
        for row in rows:
            for field in (top_field, base_field):
                if not field:
                    continue
                v = _f(row.get(field))
                if v is not None:
                    depths.append(v)

    return max(depths) if depths else 1.0


def _location_coverage(parsed: dict) -> list[dict]:
    by_loca = _rows_by_loca(parsed)
    locations = _locations(parsed)
    all_groups = _all_groups(parsed)

    rows = []

    for loc in locations:
        loca_id = loc.get("LOCA_ID", "")
        item = {"LOCA_ID": loca_id, "LOCA_TYPE": loc.get("LOCA_TYPE", "")}

        for group in all_groups:
            if group == "LOCA":
                continue
            count = len(by_loca.get(loca_id, {}).get(group, []))
            if count:
                item[group] = count

        rows.append(item)

    return rows


def _depth_events_for_location(parsed: dict, loca_id: str) -> list[dict]:
    by_loca = _rows_by_loca(parsed)
    groups = by_loca.get(loca_id, {})

    events = []

    for group, rows in groups.items():
        top_field, base_field = KNOWN_DEPTH_FIELDS.get(group, (None, None))

        if not top_field:
            continue

        for row in rows:
            top = _f(row.get(top_field))
            base = _f(row.get(base_field)) if base_field else None

            if top is None:
                continue

            label = group

            if group == "GEOL":
                label = row.get("GEOL_GEOL") or row.get("GEOL_DESC") or "GEOL"
            elif group == "SAMP":
                label = row.get("SAMP_TYPE") or row.get("SAMP_REF") or "SAMP"
            elif group == "ISPT":
                val = row.get("ISPT_NVAL") or row.get("ISPT_REP") or ""
                label = f"SPT {val}".strip()
            elif group == "WSTD":
                label = "Water"
            elif group == "CORE":
                label = f"CORE RQD {row.get('CORE_RQD', '')}".strip()
            elif group == "DCPT":
                label = row.get("DCPT_ICBR_EST") or "DCPT"
            elif group == "ICBR":
                label = f"CBR {row.get('ICBR_CBR', '')}".strip()
            elif group == "ISAT":
                label = f"SA {row.get('ISAT_TIME', '')}".strip()
            elif group == "IVAN":
                label = f"HV {row.get('IVAN_IVAN', '')}".strip()
            elif group == "IPID":
                label = f"PID {row.get('IPID_RESL', '')}".strip()

            events.append({
                "group": group,
                "top": top,
                "base": base,
                "label": str(label),
            })

    return events


def _colour(group: str) -> str:
    return {
        "GEOL": "#d9ead3",
        "SAMP": "#fff2cc",
        "ISPT": "#cfe2f3",
        "WSTD": "#9fc5e8",
        "WSTG": "#9fc5e8",
        "CORE": "#d9d2e9",
        "FRAC": "#ead1dc",
        "FRCT": "#ead1dc",
        "DCPT": "#b6d7a8",
        "ICBR": "#f4cccc",
        "ISAT": "#d0e0e3",
        "IVAN": "#ffe599",
        "IPID": "#fce5cd",
    }.get(group, "#eeeeee")


def _location_svg(parsed: dict, loca_id: str) -> str:
    max_depth = _location_max_depth(parsed, loca_id)
    events = _depth_events_for_location(parsed, loca_id)

    groups_present = sorted(set(e["group"] for e in events))
    if not groups_present:
        groups_present = ["NO_DEPTH_DATA"]

    width = 900
    height = 420
    left = 60
    right = 20
    top = 38
    bottom = 28

    plot_w = width - left - right
    plot_h = height - top - bottom

    lane_w = plot_w / len(groups_present)

    def y(depth: float) -> float:
        return top + (depth / max_depth) * plot_h

    parts = []
    parts.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">')
    parts.append('<rect width="100%" height="100%" fill="white"/>')
    parts.append(f'<rect x="{left}" y="{top}" width="{plot_w}" height="{plot_h}" fill="white" stroke="#111" stroke-width="1"/>')

    # depth grid
    depth_step = 1 if max_depth <= 10 else 2
    d = 0
    while d <= max_depth + 0.001:
        yy = y(d)
        parts.append(f'<line x1="{left}" y1="{yy:.2f}" x2="{left + plot_w}" y2="{yy:.2f}" stroke="#ddd" stroke-width="1"/>')
        parts.append(f'<text x="{left - 8}" y="{yy + 4:.2f}" font-family="Arial" font-size="12" text-anchor="end">{d:g}</text>')
        d += depth_step

    parts.append(f'<text x="{left - 38}" y="{top + plot_h / 2}" transform="rotate(-90 {left - 38} {top + plot_h / 2})" font-family="Arial" font-size="13" text-anchor="middle">Depth (m)</text>')

    # lane headers
    for idx, group in enumerate(groups_present):
        x = left + idx * lane_w
        parts.append(f'<line x1="{x:.2f}" y1="{top}" x2="{x:.2f}" y2="{top + plot_h}" stroke="#aaa" stroke-width="1"/>')
        parts.append(f'<text x="{x + lane_w / 2:.2f}" y="24" font-family="Arial" font-size="12" font-weight="bold" text-anchor="middle">{_esc(group)}</text>')

    parts.append(f'<line x1="{left + plot_w:.2f}" y1="{top}" x2="{left + plot_w:.2f}" y2="{top + plot_h}" stroke="#aaa" stroke-width="1"/>')

    # events
    group_index = {g: i for i, g in enumerate(groups_present)}

    for event in events:
        group = event["group"]
        idx = group_index[group]
        x = left + idx * lane_w
        pad = 5
        e_top = event["top"]
        e_base = event["base"]

        yy = y(e_top)
        fill = _colour(group)

        if e_base is not None and e_base > e_top:
            y2 = y(e_base)
            h = max(3, y2 - yy)
            parts.append(f'<rect x="{x + pad:.2f}" y="{yy:.2f}" width="{lane_w - pad * 2:.2f}" height="{h:.2f}" fill="{fill}" stroke="#111" stroke-width="0.7"/>')
            if h > 14:
                parts.append(f'<text x="{x + lane_w / 2:.2f}" y="{yy + 13:.2f}" font-family="Arial" font-size="10" text-anchor="middle">{_esc(event["label"])[:24]}</text>')
        else:
            parts.append(f'<circle cx="{x + lane_w / 2:.2f}" cy="{yy:.2f}" r="4" fill="{fill}" stroke="#111" stroke-width="0.7"/>')
            parts.append(f'<text x="{x + lane_w / 2:.2f}" y="{yy - 6:.2f}" font-family="Arial" font-size="9" text-anchor="middle">{_esc(event["label"])[:16]}</text>')

    parts.append(f'<text x="{left}" y="{height - 8}" font-family="Arial" font-size="11">Location { _esc(loca_id) } | Max depth {max_depth:g} m | Depth-related events: {len(events)}</text>')
    parts.append("</svg>")

    return "\n".join(parts)


def _html_table(rows: list[dict], max_rows: int = 30, max_cols: int = 12) -> str:
    if not rows:
        return "<p class='muted'>No rows.</p>"

    columns = []
    seen = set()

    for row in rows[:max_rows]:
        for key in row.keys():
            if key not in seen:
                columns.append(key)
                seen.add(key)

    columns = columns[:max_cols]

    parts = []
    parts.append("<table class='data-table'>")
    parts.append("<thead><tr>")
    for col in columns:
        parts.append(f"<th>{_esc(col)}</th>")
    parts.append("</tr></thead>")
    parts.append("<tbody>")

    for row in rows[:max_rows]:
        parts.append("<tr>")
        for col in columns:
            parts.append(f"<td>{_esc(row.get(col, ''))}</td>")
        parts.append("</tr>")

    parts.append("</tbody></table>")

    if len(rows) > max_rows:
        parts.append(f"<p class='muted'>Showing first {max_rows} of {len(rows)} rows.</p>")

    return "\n".join(parts)


def _coverage_table(rows: list[dict]) -> str:
    if not rows:
        return "<p class='muted'>No location coverage.</p>"

    columns = []
    seen = set()

    for row in rows:
        for key in row.keys():
            if key not in seen:
                columns.append(key)
                seen.add(key)

    parts = []
    parts.append("<table class='coverage-table'>")
    parts.append("<thead><tr>")
    for col in columns:
        parts.append(f"<th>{_esc(col)}</th>")
    parts.append("</tr></thead>")
    parts.append("<tbody>")

    for row in rows:
        parts.append("<tr>")
        for col in columns:
            value = row.get(col, "")
            cls = "has-data" if col not in ("LOCA_ID", "LOCA_TYPE") and value not in ("", 0, None) else ""
            parts.append(f"<td class='{cls}'>{_esc(value)}</td>")
        parts.append("</tr>")

    parts.append("</tbody></table>")
    return "\n".join(parts)


def _group_inventory(parsed: dict) -> list[dict]:
    rows = []

    for group in _all_groups(parsed):
        data = _group_rows(parsed, group)
        headings = _headings(parsed, group)
        rows.append({
            "Group": group,
            "Label": GROUP_LABELS.get(group, ""),
            "Rows": len(data),
            "Columns": len(headings),
            "Depth-aware": "Yes" if group in KNOWN_DEPTH_FIELDS and KNOWN_DEPTH_FIELDS[group][0] else "",
        })

    return rows


def build_full_report_html(parsed_list: list[dict], output_dir: Path) -> str:
    css = """
@page { size: A4; margin: 10mm; }
body { font-family: Arial, sans-serif; font-size: 9pt; color: #111; }
h1 { font-size: 20pt; margin: 0 0 6mm 0; }
h2 { font-size: 14pt; margin: 5mm 0 2mm 0; border-bottom: 1px solid #111; padding-bottom: 1mm; }
h3 { font-size: 11pt; margin: 4mm 0 2mm 0; color: #003f23; }
.page { page-break-after: always; }
.cover { display: flex; flex-direction: column; justify-content: center; height: 250mm; }
.meta { margin-top: 10mm; font-size: 10pt; }
.data-table, .coverage-table { width: 100%; border-collapse: collapse; table-layout: fixed; font-size: 7pt; }
.data-table th, .data-table td, .coverage-table th, .coverage-table td { border: 1px solid #333; padding: 1.2mm; overflow: hidden; word-break: break-word; vertical-align: top; }
.data-table th, .coverage-table th { background: #f2f2f2; font-weight: bold; }
.coverage-table .has-data { background: #d9ead3; text-align: center; font-weight: bold; }
.group-card { border: 1px solid #111; padding: 2mm; margin-bottom: 3mm; break-inside: avoid; }
.group-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 2mm; }
.stat { border: 1px solid #333; padding: 2mm; }
.stat .num { font-size: 16pt; font-weight: bold; color: #003f23; }
.muted { color: #666; font-size: 8pt; }
.loc-plot { width: 100%; border: 1px solid #111; margin: 2mm 0 5mm 0; }
.small { font-size: 7pt; }
"""

    parts = []
    parts.append("<!doctype html><html><head><meta charset='utf-8'>")
    parts.append(f"<style>{css}</style>")
    parts.append("</head><body>")

    total_groups = sum(len(_all_groups(p)) for p in parsed_list)
    total_locations = sum(len(_locations(p)) for p in parsed_list)
    total_rows = sum(sum(len(rows) for rows in p.get("groups", {}).values()) for p in parsed_list)

    parts.append("<section class='page cover'>")
    parts.append("<h1>Full AGS Data Report</h1>")
    parts.append("<p>Automated report generated from all AGS data loaded into Report Studio.</p>")
    parts.append("<div class='group-grid'>")
    parts.append(f"<div class='stat'><div class='num'>{len(parsed_list)}</div><div>AGS files</div></div>")
    parts.append(f"<div class='stat'><div class='num'>{total_groups}</div><div>Groups</div></div>")
    parts.append(f"<div class='stat'><div class='num'>{total_locations}</div><div>Locations</div></div>")
    parts.append(f"<div class='stat'><div class='num'>{total_rows}</div><div>Data rows</div></div>")
    parts.append("</div>")
    parts.append("<div class='meta'>")
    for parsed in parsed_list:
        parts.append(f"<p><b>{_esc(parsed.get('name'))}</b> — Project {_esc(_project_id(parsed))} {_esc(_project_name(parsed))}</p>")
    parts.append("</div>")
    parts.append("</section>")

    for parsed_index, parsed in enumerate(parsed_list, start=1):
        parts.append("<section class='page'>")
        parts.append(f"<h2>AGS File {parsed_index}: {_esc(parsed.get('name'))}</h2>")
        parts.append(f"<p><b>Project ID:</b> {_esc(_project_id(parsed))} &nbsp; <b>Project:</b> {_esc(_project_name(parsed))}</p>")

        inv = _group_inventory(parsed)
        parts.append("<h3>Group Inventory</h3>")
        parts.append(_html_table(inv, max_rows=80, max_cols=5))

        parts.append("<h3>Locations</h3>")
        parts.append(_html_table(_locations(parsed), max_rows=80, max_cols=8))

        parts.append("</section>")

        parts.append("<section class='page'>")
        parts.append(f"<h2>Data Coverage Matrix — {_esc(parsed.get('name'))}</h2>")
        parts.append("<p class='muted'>Cells show row counts per location/group.</p>")
        parts.append(_coverage_table(_location_coverage(parsed)))
        parts.append("</section>")

        for loc in _locations(parsed):
            loca_id = loc.get("LOCA_ID", "")
            if not loca_id:
                continue

            svg = _location_svg(parsed, loca_id)

            parts.append("<section class='page'>")
            parts.append(f"<h2>Location Data Plot — {_esc(loca_id)}</h2>")
            parts.append(f"<p><b>Type:</b> {_esc(loc.get('LOCA_TYPE'))} &nbsp; <b>Ground level:</b> {_esc(loc.get('LOCA_GL'))} &nbsp; <b>Final depth:</b> {_esc(loc.get('LOCA_FDEP'))}</p>")
            parts.append(f"<div class='loc-plot'>{svg}</div>")

            by_loca = _rows_by_loca(parsed).get(loca_id, {})
            local_summary = [
                {
                    "Group": group,
                    "Label": GROUP_LABELS.get(group, ""),
                    "Rows": len(rows),
                    "Depth-aware": "Yes" if group in KNOWN_DEPTH_FIELDS and KNOWN_DEPTH_FIELDS[group][0] else "",
                }
                for group, rows in sorted(by_loca.items())
            ]
            parts.append("<h3>Location Group Summary</h3>")
            parts.append(_html_table(local_summary, max_rows=60, max_cols=4))
            parts.append("</section>")

        for group in _all_groups(parsed):
            rows = _group_rows(parsed, group)
            label = GROUP_LABELS.get(group, "")

            parts.append("<section class='page'>")
            parts.append(f"<h2>Group Preview — {_esc(group)} {_esc(label)}</h2>")
            parts.append(f"<p><b>Rows:</b> {len(rows)} &nbsp; <b>Columns:</b> {len(_headings(parsed, group))}</p>")
            parts.append(_html_table(rows, max_rows=35, max_cols=14))
            parts.append("</section>")

    parts.append("</body></html>")
    return "\n".join(parts)


def export_full_ags_report(parsed_list: list[dict], output_dir: str | Path) -> Path:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    if not parsed_list:
        raise ValueError("No parsed AGS files supplied.")

    if len(parsed_list) == 1:
        base = _safe(_project_id(parsed_list[0])) + "_full_ags_report"
    else:
        base = "combined_full_ags_report"

    html_path = output_dir / f"{base}.html"
    pdf_path = output_dir / f"{base}.pdf"

    html_text = build_full_report_html(parsed_list, output_dir)
    html_path.write_text(html_text, encoding="utf-8")

    html_to_pdf(html_path, pdf_path)
    return pdf_path
