from __future__ import annotations

from pathlib import Path
from collections import defaultdict

from app.export.ags_csv_writer import write_project_group_zip
from app.modules.dcp.layers import icbr_rows_from_layers


def _value(value):
    return "" if value is None else str(value)


def dcp_test_to_groups(dcp_test: dict, layers: list[dict] | None = None) -> dict[str, list[dict]]:
    project_id = _value(dcp_test.get("project_id"))
    location_id = _value(dcp_test.get("location_id"))

    general = dcp_test.get("general", {}) or {}
    data = dcp_test.get("data", []) or []

    dcpg = [{
        "PROJ_ID": project_id,
        "LOCA_ID": location_id,
        "DCPG_RUN": _value(general.get("DCPG_RUN") or "1"),
        "DCPG_DATE": _value(general.get("DCPG_DATE")),
        "DCPG_TESTED_BY": _value(general.get("DCPG_TESTED_BY")),
        "DCPG_EQUIPMENT": _value(general.get("DCPG_EQUIPMENT") or "Dynamic Cone Penetrometer"),
        "DCPG_CONE_ANGLE": _value(general.get("DCPG_CONE_ANGLE")),
        "DCPG_HAMMER_MASS": _value(general.get("DCPG_HAMMER_MASS")),
        "DCPG_DROP_HEIGHT": _value(general.get("DCPG_DROP_HEIGHT")),
        "DCPG_REMARKS": _value(general.get("DCPG_REMARKS")),
    }]

    dcpt = []
    for row in data:
        dcpt.append({
            "PROJ_ID": project_id,
            "LOCA_ID": location_id,
            "DCPG_RUN": _value(row.get("DCPG_RUN") or general.get("DCPG_RUN") or "1"),
            "DCPT_BLOW": _value(row.get("DCPT_BLOW")),
            "DCPT_PEN": _value(row.get("DCPT_PEN")),
            "DCPT_DPTH": _value(row.get("DCPT_DPTH")),
            "DCPT_MM_BLOW": _value(row.get("DCPT_MM_BLOW")),
            "DCPT_ICBR_EST": _value(row.get("DCPT_ICBR_EST")),
        })

    if layers is None:
        layers = []

    icbr = icbr_rows_from_layers(dcp_test, layers) if layers else dcp_test.get("icbr_rows", [])

    return {
        "DCPG": dcpg,
        "DCPT": dcpt,
        "ICBR": icbr,
    }


def export_dcp_ags_zip_by_project(
    dcp_tests: list[dict],
    layer_store: dict[str, list[dict]],
    output_dir: str | Path,
) -> dict[str, Path]:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    by_project_location = defaultdict(lambda: defaultdict(dict))

    for test in dcp_tests:
        project_id = str(test.get("project_id") or "unknown_project").strip() or "unknown_project"
        location_id = str(test.get("location_id") or "unknown_location").strip() or "unknown_location"
        key = f"{project_id}::{location_id}"

        layers = layer_store.get(key, [])
        groups = dcp_test_to_groups(test, layers)

        by_project_location[project_id][location_id].update(groups)

    outputs = {}

    for project_id, location_groups in by_project_location.items():
        output_zip = output_dir / project_id / f"{project_id}_dcp_icbr_ags_csv.zip"
        output_zip.parent.mkdir(parents=True, exist_ok=True)
        outputs[project_id] = write_project_group_zip(project_id, dict(location_groups), output_zip)

    return outputs
