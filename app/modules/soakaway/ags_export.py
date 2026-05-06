from __future__ import annotations

from pathlib import Path
from collections import defaultdict

from app.export.ags_csv_writer import write_project_group_zip


def _value(value):
    return "" if value is None else str(value)


def soakaway_report_to_groups(report) -> dict[str, list[dict]]:
    project_id = _value(report.project.get("project_id"))
    location_id = _value(report.test.get("location_id"))
    run = _value(report.test.get("test_run") or "1")

    isag = [{
        "PROJ_ID": project_id,
        "LOCA_ID": location_id,
        "ISAG_RUN": run,
        "ISAG_DATE": _value(report.test.get("test_date")),
        "ISAG_TESTED_BY": _value(report.test.get("tested_by")),
        "ISAG_LENGTH": _value(report.pit.get("length_m")),
        "ISAG_WIDTH": _value(report.pit.get("width_m")),
        "ISAG_DEPTH": _value(report.pit.get("depth_m")),
        "ISAG_METHOD": _value(report.subfooter.get("methodology")),
        "ISAG_WEATHER": _value(report.test.get("weather")),
        "ISAG_REMARKS": _value(report.subfooter.get("remarks")),
        "ISAG_RESULT_F": _value(report.calculations.get("infiltration_rate")),
    }]

    isat = []
    for row in report.readings:
        isat.append({
            "PROJ_ID": project_id,
            "LOCA_ID": location_id,
            "ISAG_RUN": run,
            "ISAT_TIME": _value(row.get("time_min")),
            "ISAT_DPTH": _value(row.get("depth_mbgl")),
        })

    return {
        "ISAG": isag,
        "ISAT": isat,
    }


def export_soakaway_ags_zip_by_project(reports: list, output_dir: str | Path) -> dict[str, Path]:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    by_project_location = defaultdict(lambda: defaultdict(dict))

    for report in reports:
        project_id = str(report.project.get("project_id") or "unknown_project").strip() or "unknown_project"
        location_id = str(report.test.get("location_id") or "unknown_location").strip() or "unknown_location"

        groups = soakaway_report_to_groups(report)
        by_project_location[project_id][location_id].update(groups)

    outputs = {}

    for project_id, location_groups in by_project_location.items():
        output_zip = output_dir / project_id / f"{project_id}_soakaway_ags_csv.zip"
        output_zip.parent.mkdir(parents=True, exist_ok=True)
        outputs[project_id] = write_project_group_zip(project_id, dict(location_groups), output_zip)

    return outputs
