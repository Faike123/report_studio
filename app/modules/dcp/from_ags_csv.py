from __future__ import annotations


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


def dcp_tests_from_flowfinity(parsed: dict) -> list[dict]:
    tests = []

    for folder, groups in parsed["locations"].items():
        if "DCPG" not in groups and "DCPT" not in groups:
            continue

        loca = _first(groups, "LOCA")
        dcpg = _first(groups, "DCPG")
        dcpt = _rows(groups, "DCPT")

        location_id = dcpg.get("LOCA_ID") or loca.get("LOCA_ID") or folder
        project_id = dcpg.get("PROJ_ID") or loca.get("PROJ_ID") or ""

        icbr_rows = []
        for row in dcpt:
            icbr_rows.append({
                "PROJ_ID": row.get("PROJ_ID", project_id),
                "LOCA_ID": row.get("LOCA_ID", location_id),
                "ICBR_DPTH": row.get("DCPT_DPTH", ""),
                "ICBR_CBR": row.get("DCPT_ICBR_EST", ""),
                "ICBR_METHOD": "PLACEHOLDER_FROM_DCPT",
            })

        tests.append({
            "project_id": project_id,
            "location_id": location_id,
            "general": dcpg,
            "loca": loca,
            "data": dcpt,
            "row_count": len(dcpt),
            "icbr_rows": icbr_rows,
        })

    return tests
