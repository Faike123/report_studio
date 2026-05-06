from __future__ import annotations

from app.modules.borehole.strip_registry import AVAILABLE_STRIPS


LOG_WIDTH_MM = 194.0
DEPTH_LEFT_WIDTH_MM = 10.0
LEVEL_RIGHT_WIDTH_MM = 10.0
MIDDLE_WIDTH_MM = LOG_WIDTH_MM - DEPTH_LEFT_WIDTH_MM - LEVEL_RIGHT_WIDTH_MM


def _to_float(value, default=0.0):
    try:
        return float(value)
    except Exception:
        return default


def _to_bool(value):
    if isinstance(value, bool):
        return value
    return str(value).lower().strip() in ("true", "1", "yes", "y")


def build_strip_layout(layout_rows: list[dict]) -> list[dict]:
    visible_rows = []

    for row in layout_rows:
        key = row.get("key")
        if key not in AVAILABLE_STRIPS:
            continue

        visible = _to_bool(row.get("visible", False))
        if not visible:
            continue

        width = _to_float(row.get("width_mm"), AVAILABLE_STRIPS[key]["default_width_mm"])
        order = _to_float(row.get("order"), 999)

        visible_rows.append({
            "order": order,
            "key": key,
            "label": AVAILABLE_STRIPS[key]["label"],
            "width_mm": max(width, 4.0),
            "spec": AVAILABLE_STRIPS[key],
        })

    visible_rows = sorted(visible_rows, key=lambda r: r["order"])

    total_requested = sum(r["width_mm"] for r in visible_rows)

    if total_requested <= 0:
        total_requested = 1.0

    scale = MIDDLE_WIDTH_MM / total_requested

    strips = []

    x = DEPTH_LEFT_WIDTH_MM

    for row in visible_rows:
        width = row["width_mm"] * scale

        strip = {
            "key": row["key"],
            "label": row["label"],
            "x_mm": x,
            "width_mm": width,
            "spec": row["spec"],
            "lanes": [],
        }

        lane_specs = row["spec"].get("lanes", [])

        if len(lane_specs) <= 1:
            strip["lanes"].append({
                "key": lane_specs[0]["key"] if lane_specs else row["key"],
                "label": lane_specs[0]["label"] if lane_specs else row["label"],
                "x_mm": x,
                "width_mm": width,
                "kind": lane_specs[0]["kind"] if lane_specs else row["spec"]["kind"],
            })
        else:
            lx = x
            total_ratio = sum(float(lane.get("width_ratio", 1.0)) for lane in lane_specs)

            for lane in lane_specs:
                ratio = float(lane.get("width_ratio", 1.0)) / total_ratio
                lane_w = width * ratio

                strip["lanes"].append({
                    "key": lane["key"],
                    "label": lane["label"],
                    "x_mm": lx,
                    "width_mm": lane_w,
                    "kind": lane["kind"],
                })

                lx += lane_w

        strips.append(strip)
        x += width

    return strips
