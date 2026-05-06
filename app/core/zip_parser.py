from __future__ import annotations

from pathlib import Path
from zipfile import ZipFile
from collections import defaultdict
import csv
import io


KNOWN_GROUPS = [
    "LOCA",
    "DCPG",
    "DCPT",
    "ICBR",
    "ISAG",
    "ISAT",
    "GEOL",
    "SAMP",
    "HDPH",
    "IVAN",
    "IPID",
]


def detect_group(filename: str) -> str:
    name = Path(filename).name.upper()
    for group in KNOWN_GROUPS:
        if group in name:
            return group
    return "UNKNOWN"


def read_csv_bytes(raw: bytes) -> list[dict]:
    text = raw.decode("utf-8-sig", errors="replace")
    reader = csv.DictReader(io.StringIO(text))
    return [dict(row) for row in reader]


def parse_flowfinity_zip(zip_path: str | Path) -> dict:
    zip_path = Path(zip_path)

    locations = defaultdict(lambda: defaultdict(list))
    files = []
    groups_present = set()

    with ZipFile(zip_path, "r") as z:
        for member in z.namelist():
            if not member.lower().endswith(".csv"):
                continue

            p = Path(member)
            parts = p.parts
            location_folder = parts[-2] if len(parts) >= 2 else "ROOT"
            group = detect_group(p.name)

            try:
                rows = read_csv_bytes(z.read(member))
                error = ""
            except Exception as exc:
                rows = []
                error = str(exc)

            record = {
                "zip_member": member,
                "file_name": p.name,
                "group": group,
                "rows": rows,
                "row_count": len(rows),
                "error": error,
            }

            locations[location_folder][group].append(record)
            groups_present.add(group)

            files.append({
                "location": location_folder,
                "file": p.name,
                "group": group,
                "rows": len(rows),
                "error": error,
            })

    return {
        "zip_name": zip_path.name,
        "zip_path": str(zip_path),
        "locations": {k: dict(v) for k, v in locations.items()},
        "groups_present": sorted(groups_present),
        "files": files,
    }


def location_summary(parsed: dict) -> list[dict]:
    out = []
    for loc, groups in parsed["locations"].items():
        out.append({
            "location": loc,
            "groups": ", ".join(sorted(groups.keys())),
            "has_loca": "LOCA" in groups,
            "has_dcp": "DCPG" in groups or "DCPT" in groups,
            "has_soakaway": "ISAG" in groups or "ISAT" in groups,
            "file_count": sum(len(v) for v in groups.values()),
        })
    return out
