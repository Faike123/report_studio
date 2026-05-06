from __future__ import annotations

from pathlib import Path
from zipfile import ZipFile


def classify_file(path: str | Path) -> str:
    path = Path(path)

    if path.suffix.lower() == ".xlsx":
        if "soakaway" in path.name.lower():
            return "soakaway_xlsx"
        return "xlsx_unknown"

    if path.suffix.lower() == ".ags":
        return "ags_file"

    if path.suffix.lower() == ".csv":
        name = path.name.upper()
        if "DCPG" in name or "DCPT" in name:
            return "dcp_ags_csv"
        if "ISAG" in name or "ISAT" in name:
            return "soakaway_ags_csv"
        if "LOCA" in name:
            return "loca_ags_csv"
        return "csv_unknown"

    if path.suffix.lower() == ".zip":
        return classify_zip(path)

    return "unknown"


def classify_zip(path: str | Path) -> str:
    path = Path(path)

    with ZipFile(path, "r") as z:
        names = [n.upper() for n in z.namelist()]

    has_dcp = any(("DCPG" in n or "DCPT" in n) and n.endswith(".CSV") for n in names)
    has_soakaway = any(("ISAG" in n or "ISAT" in n) and n.endswith(".CSV") for n in names)
    has_loca = any("LOCA" in n and n.endswith(".CSV") for n in names)
    has_soakaway_xlsx = any(n.endswith(".XLSX") and "SOAKAWAY" in n for n in names)

    if has_dcp and has_soakaway:
        return "multi_test_ags_csv_zip"
    if has_dcp:
        return "dcp_ags_csv_zip"
    if has_soakaway:
        return "soakaway_ags_csv_zip"
    if has_soakaway_xlsx:
        return "soakaway_xlsx_zip"
    if has_loca:
        return "ags_csv_zip"

    return "zip_unknown"
