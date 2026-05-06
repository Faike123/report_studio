from __future__ import annotations

from statistics import mean, median


def _to_float(value):
    try:
        if value is None or value == "":
            return None
        return float(value)
    except Exception:
        return None


def _fmt(value, ndp=3):
    if value is None:
        return ""
    text = f"{float(value):.{ndp}f}"
    return text.rstrip("0").rstrip(".")


def dcp_points(dcp_test: dict) -> list[dict]:
    rows = []

    for row in dcp_test.get("data", []) or []:
        depth = _to_float(row.get("DCPT_DPTH"))
        blow = _to_float(row.get("DCPT_BLOW"))
        icbr = _to_float(row.get("DCPT_ICBR_EST"))
        pen = _to_float(row.get("DCPT_PEN"))
        mm_blow = _to_float(row.get("DCPT_MM_BLOW"))

        if depth is None:
            continue

        rows.append({
            "depth_m": depth,
            "blow": blow,
            "icbr": icbr,
            "penetration_mm": pen,
            "mm_blow": mm_blow,
        })

    rows.sort(key=lambda r: r["depth_m"])
    return rows


def max_depth_for_dcp(dcp_test: dict) -> float:
    points = dcp_points(dcp_test)
    if not points:
        return 0.5
    return max(p["depth_m"] for p in points)


def layers_from_break_depths(
    dcp_test: dict,
    break_depths: list[float],
    method: str = "min",
) -> list[dict]:
    max_depth = max_depth_for_dcp(dcp_test)

    cleaned = []
    for d in break_depths:
        v = _to_float(d)
        if v is None:
            continue
        if 0 < v < max_depth:
            cleaned.append(round(v, 3))

    cleaned = sorted(set(cleaned))

    depths = [0.0] + cleaned + [round(max_depth, 3)]

    layers = []
    for i in range(len(depths) - 1):
        from_m = depths[i]
        to_m = depths[i + 1]

        if to_m <= from_m:
            continue

        layers.append({
            "from_m": round(from_m, 3),
            "to_m": round(to_m, 3),
            "layer": f"Layer {i + 1}",
            "method": method,
            "manual_icbr": "",
        })

    return layers


def default_layers_for_dcp(dcp_test: dict) -> list[dict]:
    return layers_from_break_depths(dcp_test, [], method="min")


def calculate_layer_icbr(dcp_test: dict, layers: list[dict]) -> list[dict]:
    points = dcp_points(dcp_test)
    output = []

    for layer in layers:
        from_m = _to_float(layer.get("from_m"))
        to_m = _to_float(layer.get("to_m"))
        method = str(layer.get("method") or "min").lower().strip()
        manual = _to_float(layer.get("manual_icbr"))

        if from_m is None or to_m is None or to_m <= from_m:
            output.append({
                **layer,
                "point_count": 0,
                "calculated_icbr": "",
                "representative_icbr": "",
            })
            continue

        values = [
            p["icbr"]
            for p in points
            if p["icbr"] is not None and from_m <= p["depth_m"] <= to_m
        ]

        calculated = None

        if values:
            if method == "mean":
                calculated = mean(values)
            elif method == "median":
                calculated = median(values)
            elif method == "max":
                calculated = max(values)
            elif method == "manual":
                calculated = manual
            else:
                calculated = min(values)

        representative = manual if manual is not None else calculated

        output.append({
            "from_m": _fmt(from_m, 3),
            "to_m": _fmt(to_m, 3),
            "layer": layer.get("layer", ""),
            "method": method,
            "manual_icbr": _fmt(manual, 2) if manual is not None else "",
            "point_count": len(values),
            "calculated_icbr": _fmt(calculated, 2) if calculated is not None else "",
            "representative_icbr": _fmt(representative, 2) if representative is not None else "",
        })

    return output


def icbr_rows_from_layers(dcp_test: dict, layers: list[dict]) -> list[dict]:
    project_id = dcp_test.get("project_id", "")
    location_id = dcp_test.get("location_id", "")

    calculated = calculate_layer_icbr(dcp_test, layers)

    rows = []

    for idx, layer in enumerate(calculated, start=1):
        rows.append({
            "PROJ_ID": project_id,
            "LOCA_ID": location_id,
            "ICBR_ID": f"{location_id}_ICBR_{idx:03d}",
            "ICBR_FROM": layer["from_m"],
            "ICBR_TO": layer["to_m"],
            "ICBR_CBR": layer["representative_icbr"],
            "ICBR_METH": layer["method"],
            "ICBR_DESC": layer["layer"],
            "ICBR_SOURCE": "DCPG/DCPT",
        })

    return rows
