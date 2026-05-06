from __future__ import annotations

from app.core.formatters import fmt_number, fmt_date
from app.models.soakaway import empty_soakaway_report


def _first(groups: dict, code: str) -> dict:
    files = groups.get(code, [])
    if not files:
        return {}
    rows = files[0].get("rows", [])
    return rows[0] if rows else {}


def _rows(groups: dict, code: str) -> list[dict]:
    files = groups.get(code, [])
    if not files:
        return []
    return files[0].get("rows", [])


def reports_from_flowfinity(parsed: dict) -> list:
    reports = []

    for folder, groups in parsed["locations"].items():
        if "ISAG" not in groups and "ISAT" not in groups:
            continue

        loca = _first(groups, "LOCA")
        isag = _first(groups, "ISAG")
        isat = _rows(groups, "ISAT")

        report = empty_soakaway_report()

        report.project["project_id"] = isag.get("PROJ_ID") or loca.get("PROJ_ID") or ""
        report.project["project_name"] = loca.get("PROJ_NAME", "")
        report.project["client"] = loca.get("CLIENT", "")
        report.project["project_engineer"] = loca.get("PROJECT_ENGINEER", "")

        report.test["location_id"] = isag.get("LOCA_ID") or loca.get("LOCA_ID") or folder
        report.test["test_run"] = isag.get("ISAG_RUN", "1")
        report.test["test_date"] = fmt_date(isag.get("ISAG_DATE"))
        report.test["tested_by"] = isag.get("ISAG_TESTED_BY", "")
        report.test["weather"] = isag.get("ISAG_WEATHER", "")

        report.location["easting"] = fmt_number(loca.get("LOCA_NATE"))
        report.location["northing"] = fmt_number(loca.get("LOCA_NATN"))
        report.location["ground_level"] = fmt_number(loca.get("LOCA_GL"))

        report.pit["length_m"] = fmt_number(isag.get("ISAG_LENGTH"))
        report.pit["width_m"] = fmt_number(isag.get("ISAG_WIDTH"))
        report.pit["depth_m"] = fmt_number(isag.get("ISAG_DEPTH"))

        report.subfooter["remarks"] = isag.get("ISAG_REMARKS", "")
        report.subfooter["methodology"] = isag.get("ISAG_METHOD", "BRE 365 Digest rev. 2016")

        for row in isat:
            report.readings.append({
                "time_min": fmt_number(row.get("ISAT_TIME")),
                "depth_mbgl": fmt_number(row.get("ISAT_DPTH")),
            })

        reports.append(report)

    return reports
