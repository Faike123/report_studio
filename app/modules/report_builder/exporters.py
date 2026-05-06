from __future__ import annotations

from pathlib import Path
from collections import defaultdict

from app.core.pdf_merge import merge_pdfs

from app.modules.borehole.service import export_pdf as export_borehole_pdf
from app.modules.soakaway.service import export_pdf as export_soakaway_pdf
from app.modules.dcp.service import export_pdf as export_dcp_pdf

from app.modules.full_report.service import export_full_ags_report

from app.modules.dcp.ags_file_export import export_dcp_ags_file_by_project
from app.modules.soakaway.ags_file_export import export_soakaway_ags_file_by_project


def export_confirmed_items(
    items: list[dict],
    output_root: str | Path,
    borehole_reports: list,
    soakaway_reports: list,
    dcp_tests: list[dict],
    ags_files: list[dict],
    strip_layout_rows: list[dict],
    dcp_layer_store: dict[str, list[dict]],
) -> dict:
    output_root = Path(output_root)
    output_root.mkdir(parents=True, exist_ok=True)

    project_pdfs = defaultdict(list)
    project_item_outputs = defaultdict(list)

    updated_items = []

    for item in items:
        new_item = dict(item)

        if not item.get("selected"):
            updated_items.append(new_item)
            continue

        if item.get("status") not in ("confirmed", "exported"):
            updated_items.append(new_item)
            continue

        project_id = str(item.get("project_id") or "unknown_project")
        location_id = str(item.get("location_id") or "unknown_location")

        project_dir = output_root / project_id
        report_dir = project_dir / "reports"
        report_dir.mkdir(parents=True, exist_ok=True)

        try:
            pdf_path = None

            if item["item_type"] == "borehole_log":
                report = borehole_reports[item["source_index"]]
                pdf_path = export_borehole_pdf(
                    report=report,
                    output_dir=report_dir,
                    strip_layout_rows=strip_layout_rows,
                    dcp_tests=dcp_tests,
                    soakaway_reports=soakaway_reports,
                )

            elif item["item_type"] == "soakaway_report":
                report = soakaway_reports[item["source_index"]]
                pdf_path = export_soakaway_pdf(report, report_dir)

            elif item["item_type"] == "dcp_report":
                test = dcp_tests[item["source_index"]]
                key = f"{project_id}::{location_id}"
                layers = dcp_layer_store.get(key, [])
                pdf_path = export_dcp_pdf(test, report_dir, layers)

            elif item["item_type"] == "full_ags_audit":
                pdf_path = export_full_ags_report(ags_files, project_dir / "audit")

            if pdf_path:
                project_pdfs[project_id].append(Path(pdf_path))
                project_item_outputs[project_id].append(str(pdf_path))
                new_item["outputs"] = {
                    **new_item.get("outputs", {}),
                    "pdf": str(pdf_path),
                }

            new_item["status"] = "exported"
            new_item["error"] = ""

        except Exception as exc:
            new_item["status"] = "error"
            new_item["error"] = str(exc)

        updated_items.append(new_item)

    combined_outputs = {}

    for project_id, pdfs in project_pdfs.items():
        if not pdfs:
            continue

        project_dir = output_root / project_id
        combined = project_dir / f"{project_id}_COMBINED_REPORT.pdf"
        merge_pdfs(pdfs, combined)

        combined_outputs[project_id] = str(combined)

    # Export AGS where applicable. These exporters group by project internally.
    dcp_items_confirmed = [
        item for item in updated_items
        if item.get("selected")
        and item.get("item_type") == "dcp_report"
        and item.get("status") == "exported"
    ]

    soakaway_items_confirmed = [
        item for item in updated_items
        if item.get("selected")
        and item.get("item_type") == "soakaway_report"
        and item.get("status") == "exported"
    ]

    ags_outputs = {}

    if dcp_items_confirmed:
        dcp_outputs = export_dcp_ags_file_by_project(
            dcp_tests=dcp_tests,
            layer_store=dcp_layer_store,
            output_dir=output_root,
        )
        for project_id, path in dcp_outputs.items():
            ags_outputs[f"{project_id}_dcp_icbr"] = str(path)

    if soakaway_items_confirmed:
        soak_outputs = export_soakaway_ags_file_by_project(
            reports=soakaway_reports,
            output_dir=output_root,
        )
        for project_id, path in soak_outputs.items():
            ags_outputs[f"{project_id}_soakaway"] = str(path)

    return {
        "items": updated_items,
        "combined_pdfs": combined_outputs,
        "item_pdfs": dict(project_item_outputs),
        "ags_outputs": ags_outputs,
    }
