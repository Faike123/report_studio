from __future__ import annotations

from app.core.formatters import fmt_number, to_float


def _crossing(points, target):
    for i in range(len(points) - 1):
        t1, d1 = points[i]
        t2, d2 = points[i + 1]

        if d1 == target:
            return t1
        if d2 == target:
            return t2

        if min(d1, d2) <= target <= max(d1, d2) and d2 != d1:
            return t1 + ((target - d1) / (d2 - d1)) * (t2 - t1)

    return None


def calculate(report):
    length = to_float(report.pit.get("length_m"))
    width = to_float(report.pit.get("width_m"))
    pit_depth = to_float(report.pit.get("depth_m"))

    points = []
    for r in report.readings:
        t = to_float(r.get("time_min"))
        d = to_float(r.get("depth_mbgl"))
        if t is not None and d is not None:
            points.append((t, d))

    points.sort(key=lambda x: x[0])

    calc = {
        "max_effective_depth": "-",
        "depth_75": "-",
        "depth_25": "-",
        "storage_volume": "-",
        "vp_75_25": "-",
        "as50": "-",
        "time_75": "-",
        "time_25": "-",
        "t_75_25": "-",
        "infiltration_rate": "Indeterminate",
    }

    if not points or length is None or width is None or pit_depth is None:
        report.calculations = calc
        return report

    start_depth = points[0][1]
    max_eff = pit_depth - start_depth

    if max_eff <= 0:
        report.calculations = calc
        return report

    depth_75 = 0.75 * max_eff
    depth_25 = 0.25 * max_eff

    target_75_bgl = pit_depth - depth_75
    target_25_bgl = pit_depth - depth_25

    storage = length * width * max_eff
    vp = length * width * (depth_75 - depth_25)
    as50 = (2 * (length + width) * (max_eff / 2.0)) + (length * width)

    t75 = _crossing(points, target_75_bgl)
    t25 = _crossing(points, target_25_bgl)

    f = None
    seconds = None
    if t75 is not None and t25 is not None and t25 > t75:
        seconds = (t25 - t75) * 60.0
        if as50 > 0 and seconds > 0:
            f = vp / (as50 * seconds)

    calc["max_effective_depth"] = fmt_number(max_eff)
    calc["depth_75"] = fmt_number(depth_75)
    calc["depth_25"] = fmt_number(depth_25)
    calc["storage_volume"] = fmt_number(storage)
    calc["vp_75_25"] = fmt_number(vp)
    calc["as50"] = fmt_number(as50)
    calc["time_75"] = fmt_number(t75) if t75 is not None else "-"
    calc["time_25"] = fmt_number(t25) if t25 is not None else "-"
    calc["t_75_25"] = str(int(round(seconds))) if seconds is not None else "-"
    calc["infiltration_rate"] = f"{f:.5E}" if f is not None else "Indeterminate"

    report.calculations = calc
    return report
