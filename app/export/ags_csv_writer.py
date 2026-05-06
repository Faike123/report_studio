from __future__ import annotations

from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
import csv
import tempfile
import shutil


GROUP_LABELS = {
    "LOCA": "LocationDetails",
    "DCPG": "DynamicConePenetrometerTestsGeneral",
    "DCPT": "DynamicConePenetrometerTestsData",
    "ICBR": "InSituCaliforniaBearingRatioTests",
    "ISAG": "SoakawayTestsGeneral",
    "ISAT": "SoakawayTestsData",
}


def _safe(value: str) -> str:
    value = str(value or "").strip()
    if not value:
        return "UNKNOWN"
    return "".join(c if c.isalnum() or c in "-_" else "_" for c in value)


def _fieldnames(rows: list[dict]) -> list[str]:
    names = []
    seen = set()

    for row in rows:
        for key in row.keys():
            if key not in seen:
                names.append(key)
                seen.add(key)

    return names


def write_csv(path: Path, rows: list[dict], fieldnames: list[str] | None = None) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)

    if fieldnames is None:
        fieldnames = _fieldnames(rows)

    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)

    return path


def write_project_group_zip(
    project_id: str,
    location_group_rows: dict[str, dict[str, list[dict]]],
    output_zip: str | Path,
) -> Path:
    """
    location_group_rows shape:

    {
        "TP01": {
            "ISAG": [rows],
            "ISAT": [rows],
        },
        "TP02": {
            "DCPG": [rows],
            "DCPT": [rows],
            "ICBR": [rows],
        }
    }
    """
    output_zip = Path(output_zip)
    output_zip.parent.mkdir(parents=True, exist_ok=True)

    project_id_safe = _safe(project_id)

    temp_root = Path(tempfile.mkdtemp(prefix="report_studio_ags_"))

    try:
        project_dir = temp_root / project_id_safe
        project_dir.mkdir(parents=True, exist_ok=True)

        for location_id, groups in location_group_rows.items():
            location_safe = _safe(location_id)
            location_dir = project_dir / location_safe
            location_dir.mkdir(parents=True, exist_ok=True)

            for group, rows in groups.items():
                if not rows:
                    continue

                label = GROUP_LABELS.get(group, group)
                filename = f"{project_id_safe}_{location_safe}_{group}{label}.csv"
                write_csv(location_dir / filename, rows)

        if output_zip.exists():
            output_zip.unlink()

        with ZipFile(output_zip, "w", ZIP_DEFLATED) as z:
            for file in project_dir.rglob("*"):
                if file.is_file():
                    z.write(file, file.relative_to(temp_root))

        return output_zip

    finally:
        shutil.rmtree(temp_root, ignore_errors=True)
