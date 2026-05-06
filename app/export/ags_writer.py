from __future__ import annotations

from pathlib import Path
import csv
from collections import OrderedDict


DEFAULT_UNITS = {
    "LOCA": {
        "PROJ_ID": "",
        "LOCA_ID": "",
        "LOCA_TYPE": "",
        "LOCA_NATE": "m",
        "LOCA_NATN": "m",
        "LOCA_GL": "m",
        "LOCA_STAR": "yyyy-mm-dd",
        "LOCA_REM": "",
    },
    "ISAG": {
        "PROJ_ID": "",
        "LOCA_ID": "",
        "ISAG_RUN": "",
        "ISAG_DATE": "yyyy-mm-dd",
        "ISAG_TESTED_BY": "",
        "ISAG_LENGTH": "m",
        "ISAG_WIDTH": "m",
        "ISAG_DEPTH": "m",
        "ISAG_METHOD": "",
        "ISAG_WEATHER": "",
        "ISAG_REMARKS": "",
        "ISAG_RESULT_F": "m/s",
    },
    "ISAT": {
        "PROJ_ID": "",
        "LOCA_ID": "",
        "ISAG_RUN": "",
        "ISAT_TIME": "min",
        "ISAT_DPTH": "m",
    },
    "DCPG": {
        "PROJ_ID": "",
        "LOCA_ID": "",
        "DCPG_RUN": "",
        "DCPG_DATE": "yyyy-mm-dd",
        "DCPG_TESTED_BY": "",
        "DCPG_EQUIPMENT": "",
        "DCPG_CONE_ANGLE": "deg",
        "DCPG_HAMMER_MASS": "kg",
        "DCPG_DROP_HEIGHT": "mm",
        "DCPG_REMARKS": "",
    },
    "DCPT": {
        "PROJ_ID": "",
        "LOCA_ID": "",
        "DCPG_RUN": "",
        "DCPT_BLOW": "",
        "DCPT_PEN": "mm",
        "DCPT_DPTH": "m",
        "DCPT_MM_BLOW": "mm",
        "DCPT_ICBR_EST": "%",
    },
    "ICBR": {
        "PROJ_ID": "",
        "LOCA_ID": "",
        "ICBR_ID": "",
        "ICBR_FROM": "m",
        "ICBR_TO": "m",
        "ICBR_CBR": "%",
        "ICBR_METH": "",
        "ICBR_DESC": "",
        "ICBR_SOURCE": "",
    },
}


DEFAULT_TYPES = {
    "LOCA": {
        "PROJ_ID": "ID",
        "LOCA_ID": "ID",
        "LOCA_TYPE": "PA",
        "LOCA_NATE": "2DP",
        "LOCA_NATN": "2DP",
        "LOCA_GL": "2DP",
        "LOCA_STAR": "DT",
        "LOCA_REM": "X",
    },
    "ISAG": {
        "PROJ_ID": "ID",
        "LOCA_ID": "ID",
        "ISAG_RUN": "ID",
        "ISAG_DATE": "DT",
        "ISAG_TESTED_BY": "X",
        "ISAG_LENGTH": "2DP",
        "ISAG_WIDTH": "2DP",
        "ISAG_DEPTH": "2DP",
        "ISAG_METHOD": "X",
        "ISAG_WEATHER": "X",
        "ISAG_REMARKS": "X",
        "ISAG_RESULT_F": "X",
    },
    "ISAT": {
        "PROJ_ID": "ID",
        "LOCA_ID": "ID",
        "ISAG_RUN": "ID",
        "ISAT_TIME": "2DP",
        "ISAT_DPTH": "2DP",
    },
    "DCPG": {
        "PROJ_ID": "ID",
        "LOCA_ID": "ID",
        "DCPG_RUN": "ID",
        "DCPG_DATE": "DT",
        "DCPG_TESTED_BY": "X",
        "DCPG_EQUIPMENT": "X",
        "DCPG_CONE_ANGLE": "2DP",
        "DCPG_HAMMER_MASS": "2DP",
        "DCPG_DROP_HEIGHT": "2DP",
        "DCPG_REMARKS": "X",
    },
    "DCPT": {
        "PROJ_ID": "ID",
        "LOCA_ID": "ID",
        "DCPG_RUN": "ID",
        "DCPT_BLOW": "0DP",
        "DCPT_PEN": "2DP",
        "DCPT_DPTH": "2DP",
        "DCPT_MM_BLOW": "2DP",
        "DCPT_ICBR_EST": "2DP",
    },
    "ICBR": {
        "PROJ_ID": "ID",
        "LOCA_ID": "ID",
        "ICBR_ID": "ID",
        "ICBR_FROM": "2DP",
        "ICBR_TO": "2DP",
        "ICBR_CBR": "2DP",
        "ICBR_METH": "X",
        "ICBR_DESC": "X",
        "ICBR_SOURCE": "X",
    },
}


PREFERRED_ORDER = {
    "LOCA": [
        "PROJ_ID",
        "LOCA_ID",
        "LOCA_TYPE",
        "LOCA_NATE",
        "LOCA_NATN",
        "LOCA_GL",
        "LOCA_STAR",
        "LOCA_REM",
    ],
    "ISAG": [
        "PROJ_ID",
        "LOCA_ID",
        "ISAG_RUN",
        "ISAG_DATE",
        "ISAG_TESTED_BY",
        "ISAG_LENGTH",
        "ISAG_WIDTH",
        "ISAG_DEPTH",
        "ISAG_METHOD",
        "ISAG_WEATHER",
        "ISAG_REMARKS",
        "ISAG_RESULT_F",
    ],
    "ISAT": [
        "PROJ_ID",
        "LOCA_ID",
        "ISAG_RUN",
        "ISAT_TIME",
        "ISAT_DPTH",
    ],
    "DCPG": [
        "PROJ_ID",
        "LOCA_ID",
        "DCPG_RUN",
        "DCPG_DATE",
        "DCPG_TESTED_BY",
        "DCPG_EQUIPMENT",
        "DCPG_CONE_ANGLE",
        "DCPG_HAMMER_MASS",
        "DCPG_DROP_HEIGHT",
        "DCPG_REMARKS",
    ],
    "DCPT": [
        "PROJ_ID",
        "LOCA_ID",
        "DCPG_RUN",
        "DCPT_BLOW",
        "DCPT_PEN",
        "DCPT_DPTH",
        "DCPT_MM_BLOW",
        "DCPT_ICBR_EST",
    ],
    "ICBR": [
        "PROJ_ID",
        "LOCA_ID",
        "ICBR_ID",
        "ICBR_FROM",
        "ICBR_TO",
        "ICBR_CBR",
        "ICBR_METH",
        "ICBR_DESC",
        "ICBR_SOURCE",
    ],
}


def _fieldnames(group: str, rows: list[dict]) -> list[str]:
    preferred = PREFERRED_ORDER.get(group, [])
    found = OrderedDict()

    for name in preferred:
        found[name] = None

    for row in rows:
        for key in row.keys():
            if key not in found:
                found[key] = None

    return list(found.keys())


def _value(value) -> str:
    if value is None:
        return ""
    return str(value)


def write_ags_group(writer, group: str, rows: list[dict]) -> None:
    if not rows:
        return

    group = group.upper()
    headings = _fieldnames(group, rows)

    units_map = DEFAULT_UNITS.get(group, {})
    types_map = DEFAULT_TYPES.get(group, {})

    writer.writerow(["GROUP", group])
    writer.writerow(["HEADING", *headings])
    writer.writerow(["UNIT", *[units_map.get(h, "") for h in headings]])
    writer.writerow(["TYPE", *[types_map.get(h, "X") for h in headings]])

    for row in rows:
        writer.writerow(["DATA", *[_value(row.get(h, "")) for h in headings]])


def write_ags_file(groups: dict[str, list[dict]], output_path: str | Path) -> Path:
    """
    Writes AGS-like quoted comma-delimited file:

    "GROUP","ISAG"
    "HEADING","PROJ_ID","LOCA_ID",...
    "UNIT","","","m",...
    "TYPE","ID","ID","2DP",...
    "DATA","28147","TP01",...
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    group_order = ["LOCA", "ISAG", "ISAT", "DCPG", "DCPT", "ICBR"]
    remaining = [g for g in groups.keys() if g not in group_order]
    ordered = group_order + sorted(remaining)

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(
            f,
            delimiter=",",
            quotechar='"',
            quoting=csv.QUOTE_ALL,
            lineterminator="\n",
        )

        for group in ordered:
            rows = groups.get(group, [])
            if rows:
                write_ags_group(writer, group, rows)

    return output_path


def merge_group_dicts(group_dicts: list[dict[str, list[dict]]]) -> dict[str, list[dict]]:
    merged: dict[str, list[dict]] = {}

    for group_dict in group_dicts:
        for group, rows in group_dict.items():
            merged.setdefault(group, [])
            merged[group].extend(rows)

    return merged
