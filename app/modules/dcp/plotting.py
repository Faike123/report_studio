from __future__ import annotations

from pathlib import Path
import math


def _to_float(v):
    try:
        if v is None or v == "":
            return None
        return float(v)
    except Exception:
        return None


def _tick_step(xmax):
    if xmax <= 10:
        return 1
    if xmax <= 25:
        return 2
    if xmax <= 50:
        return 5
    if xmax <= 100:
        return 10
    return 20


def plot_svg(dcp_test: dict, output_path):
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    rows = dcp_test.get("data", []) or []

    pts = []
    for row in rows:
        depth = _to_float(row.get("DCPT_DPTH"))
        blow = _to_float(row.get("DCPT_BLOW"))
        if depth is not None and blow is not None:
            pts.append((blow, depth))

    pts.sort(key=lambda p: p[1])

    width = 900
    height = 520

    left = 88
    right = 18
    top = 58
    bottom = 28

    plot_w = width - left - right
    plot_h = height - top - bottom

    if not pts:
        output_path.write_text(
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}"><text x="50%" y="50%">No DCP plot data</text></svg>',
            encoding="utf-8",
        )
        return output_path

    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]

    xmin = 0.0
    xmax = max(xs) or 1.0
    ymin = 0.0
    ymax = max(ys) or 1.0

    xmax = math.ceil(xmax * 1.05)

    def sx(x):
        return left + ((x - xmin) / (xmax - xmin)) * plot_w

    def sy(y):
        return top + ((y - ymin) / (ymax - ymin)) * plot_h

    grid = []
    labels = []

    x_step = _tick_step(xmax)
    x_max_tick = int(math.ceil(xmax / x_step) * x_step)

    for val in range(0, x_max_tick + 1, x_step):
        if val > xmax:
            continue

        x = sx(val)
        grid.append(
            f'<line x1="{x:.2f}" y1="{top}" x2="{x:.2f}" y2="{top + plot_h}" stroke="#cfcfcf" stroke-width="1"/>'
        )
        labels.append(
            f'<text x="{x:.2f}" y="{top - 13}" text-anchor="middle" font-family="Arial" font-size="15">{val}</text>'
        )

    y_divs = 8
    for i in range(y_divs + 1):
        val = ymin + (ymax - ymin) * i / y_divs
        y = sy(val)

        grid.append(
            f'<line x1="{left}" y1="{y:.2f}" x2="{left + plot_w}" y2="{y:.2f}" stroke="#cfcfcf" stroke-width="1"/>'
        )
        labels.append(
            f'<text x="{left - 10}" y="{y + 5:.2f}" text-anchor="end" font-family="Arial" font-size="15">{val:.2f}</text>'
        )

    poly = " ".join(f"{sx(x):.2f},{sy(y):.2f}" for x, y in pts)

    circles = "\n".join(
        f'<circle cx="{sx(x):.2f}" cy="{sy(y):.2f}" r="3.7" fill="#003f23"/>'
        for x, y in pts
    )

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}">
<rect width="100%" height="100%" fill="white"/>
<rect x="{left}" y="{top}" width="{plot_w}" height="{plot_h}" fill="white" stroke="#333" stroke-width="1.2"/>
{"".join(grid)}
<polyline fill="none" stroke="#003f23" stroke-width="3" points="{poly}"/>
{circles}
{"".join(labels)}
<text x="{left + plot_w / 2}" y="{top - 32}" text-anchor="middle" font-family="Arial" font-size="17">Blows</text>
<text x="28" y="{top + plot_h / 2}" transform="rotate(-90 28 {top + plot_h / 2})" text-anchor="middle" font-family="Arial" font-size="17">Depth (m)</text>
</svg>'''

    output_path.write_text(svg, encoding="utf-8")
    return output_path
