from __future__ import annotations

import math


SCALE = 50
MM_PER_M = 1000 / SCALE
LOG_HEIGHT_MM = 200
DEPTH_PER_PAGE_M = LOG_HEIGHT_MM / MM_PER_M


def _to_float(value, default=0.0):
    try:
        return float(value)
    except Exception:
        return default


def borehole_pages(report) -> list[dict]:
    final_depth = _to_float(report.borehole.final_depth, 0.0)

    if final_depth <= 0:
        final_depth = 1.0

    total_pages = max(1, math.ceil(final_depth / DEPTH_PER_PAGE_M))

    pages = []

    for i in range(total_pages):
        top = i * DEPTH_PER_PAGE_M
        base = min((i + 1) * DEPTH_PER_PAGE_M, total_pages * DEPTH_PER_PAGE_M)

        pages.append({
            "page_no": i + 1,
            "total_pages": total_pages,
            "depth_from": round(top, 3),
            "depth_to": round(base, 3),
            "scale": SCALE,
            "mm_per_m": MM_PER_M,
        })

    return pages
