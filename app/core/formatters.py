from __future__ import annotations

from datetime import datetime, date


def fmt_number(value, decimals: int = 3) -> str:
    if value is None or value == "":
        return ""
    try:
        n = float(value)
        return f"{n:.{decimals}f}".rstrip("0").rstrip(".")
    except Exception:
        return str(value)


def fmt_date(value) -> str:
    if value is None or value == "":
        return ""

    if isinstance(value, datetime):
        return value.strftime("%d/%m/%Y")

    if isinstance(value, date):
        return value.strftime("%d/%m/%Y")

    text = str(value).strip()

    if text.endswith(" 00:00:00"):
        text = text[:-9]

    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(text, fmt).strftime("%d/%m/%Y")
        except Exception:
            pass

    try:
        return datetime.fromisoformat(text).strftime("%d/%m/%Y")
    except Exception:
        return text


def to_float(value):
    try:
        if value is None:
            return None
        text = str(value).strip()
        if text == "":
            return None
        return float(text)
    except Exception:
        return None
