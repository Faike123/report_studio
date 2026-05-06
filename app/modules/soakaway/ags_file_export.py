from __future__ import annotations

from pathlib import Path
from collections import defaultdict

from app.export.ags_writer import write_ags_file, merge_group_dicts
from app.modules.soakaway.ags_export import soakaway_report_to_groups


def export_soakaway_ags_file_by_project(reports: list, output_dir: str | Path) -> dict[str, Path]:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    by_project = defaultdict(list)

    for report in reports:
        project_id = str(report.project.get("project_id") or "unknown_project").strip() or "unknown_project"
        by_project[project_id].append(report)

    outputs = {}

    for project_id, project_reports in by_project.items():
        group_dicts = []

        for report in project_reports:
            group_dicts.append(soakaway_report_to_groups(report))

        groups = merge_group_dicts(group_dicts)

        out = output_dir / project_id / f"{project_id}_soakaway.ags"
        out.parent.mkdir(parents=True, exist_ok=True)

        outputs[project_id] = write_ags_file(groups, out)

    return outputs
