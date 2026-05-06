from __future__ import annotations

from pathlib import Path
from collections import defaultdict

from app.export.ags_writer import write_ags_file, merge_group_dicts
from app.modules.dcp.ags_export import dcp_test_to_groups


def export_dcp_ags_file_by_project(
    dcp_tests: list[dict],
    layer_store: dict[str, list[dict]],
    output_dir: str | Path,
) -> dict[str, Path]:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    by_project = defaultdict(list)

    for test in dcp_tests:
        project_id = str(test.get("project_id") or "unknown_project").strip() or "unknown_project"
        by_project[project_id].append(test)

    outputs = {}

    for project_id, tests in by_project.items():
        group_dicts = []

        for test in tests:
            location_id = str(test.get("location_id") or "unknown_location").strip() or "unknown_location"
            key = f"{project_id}::{location_id}"
            layers = layer_store.get(key, [])
            group_dicts.append(dcp_test_to_groups(test, layers))

        groups = merge_group_dicts(group_dicts)

        out = output_dir / project_id / f"{project_id}_dcp_icbr.ags"
        out.parent.mkdir(parents=True, exist_ok=True)

        outputs[project_id] = write_ags_file(groups, out)

    return outputs
