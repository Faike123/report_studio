from __future__ import annotations

from pathlib import Path
import html

from app.modules.borehole.layout import LOG_WIDTH_MM, DEPTH_LEFT_WIDTH_MM, LEVEL_RIGHT_WIDTH_MM
from app.modules.borehole.depth_data import matching_dcp_profile, matching_soakaway_depth_profile


LOG_HEIGHT_MM = 200.0
HEADER_HEIGHT_MM = 8.0
BODY_TOP_MM = HEADER_HEIGHT_MM
TOTAL_HEIGHT_MM = LOG_HEIGHT_MM + HEADER_HEIGHT_MM


def _f(value, default=None):
    try:
        if value in (None, ""):
            return default
        return float(value)
    except Exception:
        return default


def _esc(value):
    return html.escape("" if value is None else str(value))


def _y(depth, page):
    return BODY_TOP_MM + (depth - page["depth_from"]) * page["mm_per_m"]


def _clip_interval(top, base, page):
    top_f = _f(top)
    base_f = _f(base)

    if top_f is None or base_f is None:
        return None

    if base_f <= page["depth_from"] or top_f >= page["depth_to"]:
        return None

    visible_top = max(top_f, page["depth_from"])
    visible_base = min(base_f, page["depth_to"])

    if visible_base <= visible_top:
        return None

    return visible_top, visible_base


def _text(x, y, text, size=2.4, anchor="middle", weight="normal"):
    return f'<text x="{x:.2f}" y="{y:.2f}" font-family="Arial" font-size="{size}" text-anchor="{anchor}" font-weight="{weight}">{_esc(text)}</text>'


def _rect(x, y, w, h, fill="white", stroke="#111", sw=0.18):
    return f'<rect x="{x:.2f}" y="{y:.2f}" width="{w:.2f}" height="{h:.2f}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>'


def _line(x1, y1, x2, y2, stroke="#111", sw=0.18, dash=""):
    dash_attr = f' stroke-dasharray="{dash}"' if dash else ""
    return f'<line x1="{x1:.2f}" y1="{y1:.2f}" x2="{x2:.2f}" y2="{y2:.2f}" stroke="{stroke}" stroke-width="{sw}"{dash_attr}/>'


def render_depth_scale(page):
    parts = []
    x = 0
    w = DEPTH_LEFT_WIDTH_MM

    parts.append(_rect(x, 0, w, TOTAL_HEIGHT_MM, fill="#ffffff"))
    parts.append(_text(x + w / 2, 5, "Depth", size=2.4, weight="bold"))

    start = int(page["depth_from"])
    end = int(page["depth_to"])

    for d in range(start, end + 1):
        if d < page["depth_from"] or d > page["depth_to"]:
            continue

        y = _y(d, page)
        parts.append(_line(x + w - 2.5, y, x + w, y, sw=0.22))
        parts.append(_text(x + w - 3, y + 0.8, f"{d:g}", size=2.5, anchor="end"))

        # half metre tick
        half = d + 0.5
        if half < page["depth_to"]:
            yh = _y(half, page)
            parts.append(_line(x + w - 1.5, yh, x + w, yh, sw=0.15))

    return "\n".join(parts)


def render_level_scale(report, page):
    parts = []

    x = LOG_WIDTH_MM - LEVEL_RIGHT_WIDTH_MM
    w = LEVEL_RIGHT_WIDTH_MM

    gl = _f(report.location.ground_level, None)

    parts.append(_rect(x, 0, w, TOTAL_HEIGHT_MM, fill="#ffffff"))
    parts.append(_text(x + w / 2, 5, "Level", size=2.4, weight="bold"))

    start = int(page["depth_from"])
    end = int(page["depth_to"])

    for d in range(start, end + 1):
        if d < page["depth_from"] or d > page["depth_to"]:
            continue

        y = _y(d, page)
        label = ""
        if gl is not None:
            label = f"{gl - d:.1f}"

        parts.append(_line(x, y, x + 2.5, y, sw=0.22))
        parts.append(_text(x + 3, y + 0.8, label, size=2.2, anchor="start"))

    return "\n".join(parts)


def render_strip_headers(strips):
    parts = []

    for strip in strips:
        x = strip["x_mm"]
        w = strip["width_mm"]

        parts.append(_rect(x, 0, w, HEADER_HEIGHT_MM, fill="#f2f2f2"))
        parts.append(_text(x + w / 2, 5, strip["label"], size=2.1, weight="bold"))

        for lane in strip.get("lanes", []):
            lx = lane["x_mm"]
            lw = lane["width_mm"]
            parts.append(_line(lx, 0, lx, TOTAL_HEIGHT_MM, sw=0.12))
            if len(strip.get("lanes", [])) > 1:
                parts.append(_text(lx + lw / 2, 7.3, lane["label"], size=1.8))

        parts.append(_line(x + w, 0, x + w, TOTAL_HEIGHT_MM, sw=0.18))

    return "\n".join(parts)


def render_depth_grid(page):
    parts = []
    start = int(page["depth_from"])
    end = int(page["depth_to"])

    for d in range(start, end + 1):
        y = _y(d, page)
        parts.append(_line(0, y, LOG_WIDTH_MM, y, stroke="#d8d8d8", sw=0.12))

    return "\n".join(parts)


def render_progress(strip, report, page):
    # Placeholder for future progress intervals.
    return ""


def render_samples_tests(strip, report, page):
    parts = []
    lanes = {lane["key"]: lane for lane in strip["lanes"]}

    sample_lane = lanes.get("samples")
    spt_lane = lanes.get("spt")

    if sample_lane:
        x = sample_lane["x_mm"]
        w = sample_lane["width_mm"]

        for sample in report.borehole.samples:
            clipped = _clip_interval(sample.get("top"), sample.get("base") or sample.get("top"), page)
            if clipped is None:
                depth = _f(sample.get("top"))
                if depth is None or depth < page["depth_from"] or depth > page["depth_to"]:
                    continue
                y = _y(depth, page)
                parts.append(_text(x + w / 2, y + 1, sample.get("type", "S"), size=2.2))
                continue

            top, base = clipped
            y = _y(top, page)
            h = max(2.0, (base - top) * page["mm_per_m"])
            parts.append(_rect(x + 1, y, w - 2, h, fill="#ffffff", stroke="#111", sw=0.14))
            label = sample.get("type") or sample.get("reference") or "S"
            parts.append(_text(x + w / 2, y + min(h / 2 + 0.8, h - 0.3), label, size=2.0))

    if spt_lane:
        x = spt_lane["x_mm"]
        w = spt_lane["width_mm"]

        for test in report.borehole.tests:
            depth = _f(test.get("depth"))
            if depth is None or depth < page["depth_from"] or depth > page["depth_to"]:
                continue

            y = _y(depth, page)
            result = test.get("result", "")
            label = f"N={result}" if result and not str(result).startswith("N") else str(result)
            parts.append(_line(x + 1, y, x + w - 1, y, stroke="#003f23", sw=0.35))
            parts.append(_text(x + w / 2, y - 0.8, label, size=1.9))

    return "\n".join(parts)


def render_water_installation(strip, report, page):
    parts = []
    lanes = {lane["key"]: lane for lane in strip["lanes"]}
    water_lane = lanes.get("water")

    if water_lane:
        x = water_lane["x_mm"]
        w = water_lane["width_mm"]

        for water in report.borehole.groundwater:
            depth = _f(water.get("depth"))
            if depth is None or depth < page["depth_from"] or depth > page["depth_to"]:
                continue

            y = _y(depth, page)
            parts.append(f'<polygon points="{x + w/2:.2f},{y - 1.6:.2f} {x + w/2 - 1.8:.2f},{y + 1.6:.2f} {x + w/2 + 1.8:.2f},{y + 1.6:.2f}" fill="#3b78ff" stroke="#111" stroke-width="0.12"/>')

    return "\n".join(parts)


def render_casing_backfill(strip, report, page):
    # Placeholder: supports future casing/backfill intervals.
    return ""


def legend_fill(legend):
    text = str(legend or "").upper()

    if "CLAY" in text:
        return "#d9b38c"
    if "SAND" in text:
        return "#fff2a6"
    if "GRAVEL" in text:
        return "#d0d0d0"
    if "TOP" in text:
        return "#9ccc65"
    if "PEAT" in text:
        return "#6d4c41"
    if "ROCK" in text or "MUDSTONE" in text or "SANDSTONE" in text:
        return "#b0bec5"

    return "#eeeeee"


def render_legend(strip, report, page):
    parts = []
    lane = strip["lanes"][0]
    x = lane["x_mm"]
    w = lane["width_mm"]

    for row in report.borehole.strata:
        clipped = _clip_interval(row.get("top"), row.get("base"), page)
        if clipped is None:
            continue

        top, base = clipped
        y = _y(top, page)
        h = (base - top) * page["mm_per_m"]
        fill = legend_fill(row.get("legend") or row.get("description"))

        parts.append(_rect(x, y, w, h, fill=fill, stroke="#111", sw=0.14))

        # simple hatch lines
        for i in range(0, int(max(h, 1)) + 4, 4):
            parts.append(_line(x, y + i, x + w, y + i - 4, stroke="#777", sw=0.08))

    return "\n".join(parts)


def render_description(strip, report, page):
    parts = []
    lane = strip["lanes"][0]
    x = lane["x_mm"]
    w = lane["width_mm"]

    for row in report.borehole.strata:
        clipped = _clip_interval(row.get("top"), row.get("base"), page)
        if clipped is None:
            continue

        top, base = clipped
        y = _y(top, page)
        h = (base - top) * page["mm_per_m"]

        parts.append(_rect(x, y, w, h, fill="#ffffff", stroke="#111", sw=0.14))

        desc = str(row.get("description", "")).strip()
        if not desc:
            desc = str(row.get("legend", "")).strip()

        # simple line wrapping by character count based on width
        approx_chars = max(18, int(w * 1.25))
        words = desc.split()
        lines = []
        current = ""

        for word in words:
            if len(current + " " + word) <= approx_chars:
                current = (current + " " + word).strip()
            else:
                lines.append(current)
                current = word

        if current:
            lines.append(current)

        max_lines = max(1, int(h / 3.2))

        for idx, line in enumerate(lines[:max_lines]):
            parts.append(_text(x + 1.2, y + 3.0 + idx * 3.0, line, size=2.2, anchor="start"))

    return "\n".join(parts)


def render_rock_quality(strip, report, page):
    parts = []
    lanes = {lane["key"]: lane for lane in strip["lanes"]}

    for row in report.borehole.rock:
        clipped = _clip_interval(row.get("top"), row.get("base"), page)
        if clipped is None:
            continue

        top, base = clipped
        y = _y(top, page)
        h = max(2.5, (base - top) * page["mm_per_m"])

        for key in ("tcr", "scr", "rqd"):
            lane = lanes.get(key)
            if not lane:
                continue

            x = lane["x_mm"]
            w = lane["width_mm"]
            value = row.get(key, "")

            parts.append(_rect(x, y, w, h, fill="#ffffff", stroke="#111", sw=0.12))
            parts.append(_text(x + w / 2, y + min(h / 2 + 0.7, h - 0.3), value, size=1.9))

    return "\n".join(parts)


def render_dcp_profile(strip, report, page, dcp_tests):
    profile = matching_dcp_profile(report, dcp_tests)
    if not profile:
        return ""

    lane = strip["lanes"][0]
    x = lane["x_mm"]
    w = lane["width_mm"]

    values = [p["blow"] for p in profile if p.get("blow") is not None]
    if not values:
        return ""

    vmax = max(values) or 1

    pts = []
    for p in profile:
        depth = p.get("depth")
        value = p.get("blow")

        if depth is None or value is None:
            continue
        if depth < page["depth_from"] or depth > page["depth_to"]:
            continue

        px = x + (value / vmax) * (w - 1.5)
        py = _y(depth, page)
        pts.append((px, py))

    parts = []
    if len(pts) >= 2:
        poly = " ".join(f"{px:.2f},{py:.2f}" for px, py in pts)
        parts.append(f'<polyline fill="none" stroke="#003f23" stroke-width="0.35" points="{poly}"/>')

    for px, py in pts:
        parts.append(f'<circle cx="{px:.2f}" cy="{py:.2f}" r="0.7" fill="#003f23"/>')

    return "\n".join(parts)


def render_icbr_profile(strip, report, page, dcp_tests):
    profile = matching_dcp_profile(report, dcp_tests)
    if not profile:
        return ""

    lane = strip["lanes"][0]
    x = lane["x_mm"]
    w = lane["width_mm"]

    values = [p["icbr"] for p in profile if p.get("icbr") is not None]
    if not values:
        return ""

    vmax = max(values) or 1

    pts = []
    for p in profile:
        depth = p.get("depth")
        value = p.get("icbr")

        if depth is None or value is None:
            continue
        if depth < page["depth_from"] or depth > page["depth_to"]:
            continue

        px = x + (value / vmax) * (w - 1.5)
        py = _y(depth, page)
        pts.append((px, py))

    parts = []
    if len(pts) >= 2:
        poly = " ".join(f"{px:.2f},{py:.2f}" for px, py in pts)
        parts.append(f'<polyline fill="none" stroke="#8b0000" stroke-width="0.35" points="{poly}"/>')

    for px, py in pts:
        parts.append(f'<circle cx="{px:.2f}" cy="{py:.2f}" r="0.7" fill="#8b0000"/>')

    return "\n".join(parts)


def render_soakaway_depth(strip, report, page, soakaway_reports):
    profile = matching_soakaway_depth_profile(report, soakaway_reports)
    if not profile:
        return ""

    lane = strip["lanes"][0]
    x = lane["x_mm"]
    w = lane["width_mm"]

    values = [p["time_min"] for p in profile if p.get("time_min") is not None]
    if not values:
        return ""

    vmax = max(values) or 1

    pts = []
    for p in profile:
        depth = p.get("depth")
        value = p.get("time_min")

        if depth is None or value is None:
            continue
        if depth < page["depth_from"] or depth > page["depth_to"]:
            continue

        px = x + (value / vmax) * (w - 1.5)
        py = _y(depth, page)
        pts.append((px, py))

    parts = []
    if len(pts) >= 2:
        poly = " ".join(f"{px:.2f},{py:.2f}" for px, py in pts)
        parts.append(f'<polyline fill="none" stroke="#005f99" stroke-width="0.35" points="{poly}"/>')

    for px, py in pts:
        parts.append(f'<circle cx="{px:.2f}" cy="{py:.2f}" r="0.7" fill="#005f99"/>')

    return "\n".join(parts)


def render_strip_content(strip, report, page, dcp_tests=None, soakaway_reports=None):
    key = strip["key"]

    if key == "progress":
        return render_progress(strip, report, page)
    if key == "samples_tests":
        return render_samples_tests(strip, report, page)
    if key == "water_installation":
        return render_water_installation(strip, report, page)
    if key == "casing_backfill":
        return render_casing_backfill(strip, report, page)
    if key == "legend":
        return render_legend(strip, report, page)
    if key == "description":
        return render_description(strip, report, page)
    if key == "rock_quality":
        return render_rock_quality(strip, report, page)
    if key == "dcp_profile":
        return render_dcp_profile(strip, report, page, dcp_tests)
    if key == "icbr_profile":
        return render_icbr_profile(strip, report, page, dcp_tests)
    if key == "soakaway_depth":
        return render_soakaway_depth(strip, report, page, soakaway_reports)

    return ""


def render_borehole_svg(
    report,
    page: dict,
    strips: list[dict],
    output_path: str | Path,
    dcp_tests: list[dict] | None = None,
    soakaway_reports: list | None = None,
):
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    parts = []

    parts.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{LOG_WIDTH_MM}mm" height="{TOTAL_HEIGHT_MM}mm" viewBox="0 0 {LOG_WIDTH_MM} {TOTAL_HEIGHT_MM}">')
    parts.append(_rect(0, 0, LOG_WIDTH_MM, TOTAL_HEIGHT_MM, fill="#ffffff", stroke="#111", sw=0.2))
    parts.append(render_depth_grid(page))
    parts.append(render_depth_scale(page))
    parts.append(render_level_scale(report, page))
    parts.append(render_strip_headers(strips))

    for strip in strips:
        parts.append(render_strip_content(strip, report, page, dcp_tests, soakaway_reports))

    parts.append(_line(0, HEADER_HEIGHT_MM, LOG_WIDTH_MM, HEADER_HEIGHT_MM, sw=0.22))
    parts.append("</svg>")

    output_path.write_text("\n".join(parts), encoding="utf-8")
    return output_path
