from __future__ import annotations

from pathlib import Path
import csv
from collections import defaultdict


def _clean(value):
    if value is None:
        return ""
    return str(value).strip()


def parse_ags_file(path: str | Path) -> dict:
    """
    Basic AGS parser for quoted AGS4-style files.

    Supports:
    "GROUP","LOCA"
    "HEADING","LOCA_ID","LOCA_TYPE",...
    "UNIT","","",...
    "TYPE","ID","X",...
    "DATA","BH01","CP",...
    """
    path = Path(path)

    groups = defaultdict(list)
    headings = {}
    units = {}
    types = {}

    current_group = None
    current_headings = []

    with open(path, "r", encoding="utf-8-sig", errors="replace", newline="") as f:
        reader = csv.reader(f)

        for raw_row in reader:
            if not raw_row:
                continue

            row = [_clean(x) for x in raw_row]
            tag = row[0].upper() if row else ""

            if tag == "GROUP":
                current_group = row[1].upper() if len(row) > 1 else None
                current_headings = []

            elif tag == "HEADING" and current_group:
                current_headings = row[1:]
                headings[current_group] = current_headings

            elif tag == "UNIT" and current_group:
                units[current_group] = row[1:]

            elif tag == "TYPE" and current_group:
                types[current_group] = row[1:]

            elif tag == "DATA" and current_group and current_headings:
                values = row[1:]
                record = {}

                for i, heading in enumerate(current_headings):
                    record[heading] = values[i] if i < len(values) else ""

                groups[current_group].append(record)

    return {
        "path": str(path),
        "name": path.name,
        "groups": dict(groups),
        "headings": headings,
        "units": units,
        "types": types,
    }


def ags_summary(parsed: dict) -> list[dict]:
    rows = []

    for group, data_rows in sorted(parsed.get("groups", {}).items()):
        rows.append({
            "group": group,
            "rows": len(data_rows),
            "columns": len(parsed.get("headings", {}).get(group, [])),
        })

    return rows
