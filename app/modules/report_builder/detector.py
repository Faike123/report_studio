from __future__ import annotations

from collections import defaultdict


REPORTABLE_GROUPS = {
    "LOCA",
    "GEOL",
    "SAMP",
    "ISPT",
    "WSTD",
    "WSTG",
    "CORE",
    "FRAC",
    "FRCT",
    "DCPG",
    "DCPT",
    "ICBR",
    "ISAG",
    "ISAT",
}

KNOWN_GROUP_LABELS = {
    "PROJ": "Project information",
    "LOCA": "Location details",
    "GEOL": "Geology descriptions",
    "SAMP": "Samples",
    "ISPT": "SPT tests",
    "WSTD": "Groundwater / water observations",
    "WSTG": "Groundwater / water observations",
    "CORE": "Core recovery",
    "FRAC": "Fractures",
    "FRCT": "Fractures",
    "DCPG": "DCP general",
    "DCPT": "DCP data",
    "ICBR": "In-situ CBR",
    "ISAG": "Soakaway general",
    "ISAT": "Soakaway readings",
    "IVAN": "Hand vane",
    "IPID": "PID results",
    "ERES": "Electrical resistivity",
    "LLPL": "Liquid / plastic limit",
    "MC": "Moisture content",
    "GRAG": "Particle size distribution",
    "GCHM": "Geochemistry",
    "CONG": "Contamination general",
    "MOND": "Monitoring details",
    "PIPE": "Installation pipe",
    "BACK": "Backfill",
}

PDF_ENGINE_GROUPS = {
    "borehole_log": {"LOCA", "GEOL"},
    "soakaway_report": {"ISAG", "ISAT"},
    "dcp_report": {"DCPG", "DCPT"},
}

EXPORT_ONLY_DEFAULT_SELECTED = True


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


def _project_id_from_parsed_ags(parsed: dict) -> str:
    groups = parsed.get("groups", {})
    proj = groups.get("PROJ", [])
    loca = groups.get("LOCA", [])

    if proj and proj[0].get("PROJ_ID"):
        return str(proj[0].get("PROJ_ID"))

    if loca and loca[0].get("PROJ_ID"):
        return str(loca[0].get("PROJ_ID"))

    return str(parsed.get("name", "unknown_project")).replace(".ags", "")


def _loca_ids_from_group_rows(rows: list[dict]) -> list[str]:
    ids = sorted({
        str(row.get("LOCA_ID", "")).strip()
        for row in rows
        if str(row.get("LOCA_ID", "")).strip()
    })
    return ids


def _group_summary_item(
    parsed_index: int,
    project_id: str,
    group: str,
    rows: list[dict],
    headings: list[str],
) -> dict:
    label = KNOWN_GROUP_LABELS.get(group, "Custom / unclassified AGS group")
    loca_ids = _loca_ids_from_group_rows(rows)

    is_known = group in KNOWN_GROUP_LABELS
    is_reportable_source = group in REPORTABLE_GROUPS

    if is_reportable_source:
        status = "data_detected"
        category = "report_source_data"
    elif is_known:
        status = "export_ready"
        category = "ags_export_only"
    else:
        status = "unclassified"
        category = "custom_group"

    return {
        "item_id": f"{project_id}::AGS_GROUP::{group}::{parsed_index}",
        "project_id": project_id,
        "location_id": "MULTI" if loca_ids else "PROJECT",
        "item_type": "ags_group_data",
        "data_category": category,
        "label": f"{group} — {label}",
        "source_index": parsed_index,
        "selected": EXPORT_ONLY_DEFAULT_SELECTED,
        "status": status,
        "requires_review": False,
        "dependency": "",
        "summary": f"{len(rows)} rows | {len(headings)} columns | {len(loca_ids)} locations",
        "config": {
            "group": group,
            "row_count": len(rows),
            "column_count": len(headings),
            "location_count": len(loca_ids),
            "locations": loca_ids,
            "has_pdf_engine": is_reportable_source,
            "known_group": is_known,
        },
        "outputs": {},
        "error": "",
    }


def _location_group_items(
    parsed_index: int,
    project_id: str,
    group: str,
    rows: list[dict],
) -> list[dict]:
    by_loca = defaultdict(list)

    for row in rows:
        loca_id = str(row.get("LOCA_ID", "")).strip()
        if loca_id:
            by_loca[loca_id].append(row)

    items = []

    for loca_id, local_rows in sorted(by_loca.items()):
        label = KNOWN_GROUP_LABELS.get(group, "Custom / unclassified AGS group")
        is_known = group in KNOWN_GROUP_LABELS
        is_reportable_source = group in REPORTABLE_GROUPS

        if is_reportable_source:
            category = "location_report_source_data"
            status = "data_detected"
        elif is_known:
            category = "location_export_only"
            status = "export_ready"
        else:
            category = "location_custom_group"
            status = "unclassified"

        items.append({
            "item_id": f"{project_id}::{loca_id}::AGS_LOCATION_GROUP::{group}::{parsed_index}",
            "project_id": project_id,
            "location_id": loca_id,
            "item_type": "ags_location_group_data",
            "data_category": category,
            "label": f"{loca_id} {group} — {label}",
            "source_index": parsed_index,
            "selected": False,
            "status": status,
            "requires_review": False,
            "dependency": "",
            "summary": f"{len(local_rows)} rows at location {loca_id}",
            "config": {
                "group": group,
                "row_count": len(local_rows),
                "has_pdf_engine": is_reportable_source,
                "known_group": is_known,
            },
            "outputs": {},
            "error": "",
        })

    return items


def detect_report_items(
    borehole_reports: list,
    soakaway_reports: list,
    dcp_tests: list[dict],
    ags_files: list[dict],
) -> list[dict]:
    """
    Creates a flat queue of:
    - production PDF report items
    - exportable AGS group data
    - location-level AGS group data
    - custom/unclassified data groups
    - full audit appendices
    """
    items = []

    # ------------------------------------------------------------------
    # 1. PDF/report-engine items
    # ------------------------------------------------------------------

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
            "data_category": "pdf_report",
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
                "source_groups": ["LOCA", "GEOL", "SAMP", "ISPT", "WSTD", "CORE", "FRAC"],
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
            "data_category": "pdf_report",
            "label": f"{location_id} Soakaway Run {run}",
            "source_index": idx,
            "selected": True,
            "status": "needs_review",
            "requires_review": True,
            "dependency": "",
            "summary": f"Run {run} | f = {f_value}",
            "config": {
                "run": run,
                "source_groups": ["ISAG", "ISAT"],
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
            "data_category": "pdf_report",
            "label": f"{location_id} DCP / ICBR Report",
            "source_index": idx,
            "selected": True,
            "status": "needs_review",
            "requires_review": True,
            "dependency": "ICBR export depends on confirmed DCP layers",
            "summary": f"{row_count} DCPT rows",
            "config": {
                "layer_method": "min",
                "source_groups": ["DCPG", "DCPT", "ICBR"],
            },
            "outputs": {},
            "error": "",
        })

    # ------------------------------------------------------------------
    # 2. Full AGS scan. This ensures all data is detected, even if no PDF
    #    engine exists yet.
    # ------------------------------------------------------------------

    for parsed_index, parsed in enumerate(ags_files or []):
        groups = parsed.get("groups", {})
        headings = parsed.get("headings", {})
        project_id = _project_id_from_parsed_ags(parsed)

        items.append({
            "item_id": f"{project_id}::AGS_AUDIT::{parsed_index}",
            "project_id": project_id,
            "location_id": "ALL",
            "item_type": "full_ags_audit",
            "data_category": "audit_report",
            "label": f"{project_id} Full AGS Audit Appendix",
            "source_index": parsed_index,
            "selected": False,
            "status": "detected",
            "requires_review": False,
            "dependency": "",
            "summary": f"{len(groups)} groups | {sum(len(v) for v in groups.values())} rows",
            "config": {
                "groups": sorted(groups.keys()),
            },
            "outputs": {},
            "error": "",
        })

        for group, rows in sorted(groups.items()):
            group_headings = headings.get(group, [])
            items.append(
                _group_summary_item(
                    parsed_index=parsed_index,
                    project_id=project_id,
                    group=group,
                    rows=rows,
                    headings=group_headings,
                )
            )

            # Location-level data inventory. These are not selected by default,
            # because they are mostly for traceability and future strip/report engines.
            items.extend(
                _location_group_items(
                    parsed_index=parsed_index,
                    project_id=project_id,
                    group=group,
                    rows=rows,
                )
            )

    return items


def queue_summary(items: list[dict]) -> dict:
    by_status = defaultdict(int)
    by_type = defaultdict(int)
    by_project = defaultdict(int)
    by_category = defaultdict(int)

    for item in items:
        by_status[item.get("status", "unknown")] += 1
        by_type[item.get("item_type", "unknown")] += 1
        by_project[item.get("project_id", "unknown_project")] += 1
        by_category[item.get("data_category", "unknown")] += 1

    return {
        "total": len(items),
        "selected": sum(1 for i in items if i.get("selected")),
        "confirmed": sum(1 for i in items if i.get("status") == "confirmed"),
        "exported": sum(1 for i in items if i.get("status") == "exported"),
        "by_status": dict(by_status),
        "by_type": dict(by_type),
        "by_project": dict(by_project),
        "by_category": dict(by_category),
    }


def queue_table(items: list[dict]) -> list[dict]:
    rows = []

    for idx, item in enumerate(items):
        rows.append({
            "queue_index": idx,
            "selected": bool(item.get("selected", False)),
            "status": item.get("status", ""),
            "data_category": item.get("data_category", ""),
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
        if item.get("selected")
        and item.get("requires_review")
        and item.get("item_type") not in ("full_ags_audit", "ags_group_data", "ags_location_group_data")
    ]


def next_unconfirmed_index(items: list[dict]) -> int | None:
    for idx, item in enumerate(items):
        if not item.get("selected"):
            continue
        if not item.get("requires_review"):
            continue
        if item.get("status") not in ("confirmed", "excluded", "exported"):
            return idx
    return None
