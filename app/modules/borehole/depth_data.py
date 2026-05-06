from __future__ import annotations


def _to_float(value):
    try:
        if value is None or value == "":
            return None
        return float(value)
    except Exception:
        return None


def matching_dcp_profile(report, dcp_tests: list[dict] | None) -> list[dict]:
    if not dcp_tests:
        return []

    location_id = str(report.test.location_id)

    out = []

    for test in dcp_tests:
        if str(test.get("location_id", "")) != location_id:
            continue

        for row in test.get("data", []) or []:
            depth = _to_float(row.get("DCPT_DPTH"))
            blow = _to_float(row.get("DCPT_BLOW"))
            icbr = _to_float(row.get("DCPT_ICBR_EST"))

            if depth is None:
                continue

            out.append({
                "depth": depth,
                "blow": blow,
                "icbr": icbr,
            })

    return sorted(out, key=lambda r: r["depth"])


def matching_soakaway_depth_profile(report, soakaway_reports: list | None) -> list[dict]:
    if not soakaway_reports:
        return []

    location_id = str(report.test.location_id)

    out = []

    for sa in soakaway_reports:
        if str(sa.test.get("location_id", "")) != location_id:
            continue

        pit_depth = _to_float(sa.pit.get("depth_m"))

        for row in sa.readings:
            time_min = _to_float(row.get("time_min"))
            depth = _to_float(row.get("depth_mbgl"))

            if depth is None:
                continue

            out.append({
                "depth": depth,
                "time_min": time_min,
                "pit_depth": pit_depth,
            })

    return sorted(out, key=lambda r: r["depth"])
