from __future__ import annotations

from collections import defaultdict


def _get(obj, key, default=""):
    if obj is None:
        return default

    if isinstance(obj, dict):
        return obj.get(key, default)

    return getattr(obj, key, default)


def _project_id_from_borehole(report) -> str:
    return str(_get(report.project, "project_id", "unknown_project") or "unknown_project")


def _location_id_from_borehole(report) -> str:
    return str(_get(report.test, "location_id", "unknown_location") or "unknown_location")


def _project_id_from_soakaway(report) -> str:
    return str(report.project.get("project_id") or "unknown_project")


def _location_id_from_soakaway(report) -> str:
    return str(report.test.get("location_id") or "unknown_location")


def _project_id_from_dcp(test: dict) -> str:
    return str(test.get("project_id") or "unknown_project")


def _location_id_from_dcp(test: dict) -> str:
    return str(test.get("location_id") or "unknown_location")


def detect_report_items(
    borehole_reports: list,
    soakaway_reports: list,
    dcp_tests: list[dict],
    ags_files: list[dict],
) -> list[dict]:
    """
    Creates a flat queue of reportable production items.

    Each item is intentionally lightweight. The heavy object is referenced by
    source_index and loaded from Streamlit session state during review/export.
    """
    items = []

    for idx, report in enumerate(borehole_reports or []):
        project_id = _project_id_from_borehole(report)
        location_id = _location_id_from_borehole(report)

        final_depth = _get(report.borehole, "final_depth", "")
        bh_type = _get(report.borehole, "type", "")

        items.append({
            "item_id": f"{project_id}::{location_id}::borehole_log::{idx}",
            "project_id": project_id,
            "location_id": location_id,
            "item_type": "borehole_log",
            "label": f"{location_id} Borehole Log",
            "source_index": idx,
            "selected": True,
            "status": "needs_review",
            "requires_review": True,
            "dependency": "",
            "summary": f"{bh_type} | final depth {final_depth} m",
            "config": {
                "scale": 50,
                "strip_layout_source": "global",
            },
            "outputs": {},
            "error": "",
        })

    for idx, report in enumerate(soakaway_reports or []):
        project_id = _project_id_from_soakaway(report)
        location_id = _location_id_from_soakaway(report)
        run = str(report.test.get("test_run") or "1")

        f_value = report.calculations.get("infiltration_rate") if hasattr(report, "calculations") else ""

        items.append({
            "item_id": f"{project_id}::{location_id}::soakaway::{run}::{idx}",
            "project_id": project_id,
            "location_id": location_id,
            "item_type": "soakaway_report",
            "label": f"{location_id} Soakaway Run {run}",
            "source_index": idx,
            "selected": True,
            "status": "needs_review",
            "requires_review": True,
            "dependency": "",
            "summary": f"Run {run} | f = {f_value}",
            "config": {
                "run": run,
            },
            "outputs": {},
            "error": "",
        })

    for idx, test in enumerate(dcp_tests or []):
        project_id = _project_id_from_dcp(test)
        location_id = _location_id_from_dcp(test)
        row_count = len(test.get("data", []) or [])

        items.append({
            "item_id": f"{project_id}::{location_id}::dcp_report::{idx}",
            "project_id": project_id,
            "location_id": location_id,
            "item_type": "dcp_report",
            "label": f"{location_id} DCP / ICBR Report",
            "source_index": idx,
            "selected": True,
            "status": "needs_review",
            "requires_review": True,
            "dependency": "ICBR export depends on confirmed DCP layers",
            "summary": f"{row_count} DCPT rows",
            "config": {
                "layer_method": "min",
            },
            "outputs": {},
            "error": "",
        })

    for idx, parsed in enumerate(ags_files or []):
        groups = parsed.get("groups", {})
        project_id = "unknown_project"

        loca = groups.get("LOCA", [])
        proj = groups.get("PROJ", [])

        if proj and proj[0].get("PROJ_ID"):
            project_id = str(proj[0].get("PROJ_ID"))
        elif loca and loca[0].get("PROJ_ID"):
            project_id = str(loca[0].get("PROJ_ID"))

        items.append({
            "item_id": f"{project_id}::AGS_AUDIT::{idx}",
            "project_id": project_id,
            "location_id": "ALL",
            "item_type": "full_ags_audit",
            "label": f"{project_id} Full AGS Audit Appendix",
            "source_index": idx,
            "selected": False,
            "status": "detected",
            "requires_review": False,
            "dependency": "",
            "summary": f"{len(groups)} groups | {sum(len(v) for v in groups.values())} rows",
            "config": {},
            "outputs": {},
            "error": "",
        })

    return items


def queue_summary(items: list[dict]) -> dict:
    by_status = defaultdict(int)
    by_type = defaultdict(int)
    by_project = defaultdict(int)

    for item in items:
        by_status[item.get("status", "unknown")] += 1
        by_type[item.get("item_type", "unknown")] += 1
        by_project[item.get("project_id", "unknown_project")] += 1

    return {
        "total": len(items),
        "selected": sum(1 for i in items if i.get("selected")),
        "confirmed": sum(1 for i in items if i.get("status") == "confirmed"),
        "exported": sum(1 for i in items if i.get("status") == "exported"),
        "by_status": dict(by_status),
        "by_type": dict(by_type),
        "by_project": dict(by_project),
    }


def queue_table(items: list[dict]) -> list[dict]:
    rows = []

    for idx, item in enumerate(items):
        rows.append({
            "queue_index": idx,
            "selected": bool(item.get("selected", False)),
            "status": item.get("status", ""),
            "project_id": item.get("project_id", ""),
            "location_id": item.get("location_id", ""),
            "item_type": item.get("item_type", ""),
            "label": item.get("label", ""),
            "summary": item.get("summary", ""),
            "dependency": item.get("dependency", ""),
        })

    return rows


def selected_review_indices(items: list[dict]) -> list[int]:
    return [
        idx for idx, item in enumerate(items)
        if item.get("selected") and item.get("item_type") != "full_ags_audit"
    ]


def next_unconfirmed_index(items: list[dict]) -> int | None:
    for idx, item in enumerate(items):
        if not item.get("selected"):
            continue
        if item.get("item_type") == "full_ags_audit":
            continue
        if item.get("status") not in ("confirmed", "excluded", "exported"):
            return idx
    return None
