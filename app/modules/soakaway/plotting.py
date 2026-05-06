from __future__ import annotations

from pathlib import Path
import math

from app.core.formatters import to_float


def _tick_step(xmax):
    if xmax <= 10:
        return 1
    if xmax <= 20:
        return 2
    if xmax <= 60:
        return 10
    if xmax <= 180:
        return 15
    return 30


def plot_svg(report, output_path):
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    pts = []
    for row in report.readings:
        t = to_float(row.get("time_min"))
        d = to_float(row.get("depth_mbgl"))
        if t is not None and d is not None:
            pts.append((t, d))

    width = 900
    height = 520

    left = 82
    right = 20
    top = 58
    bottom = 26

    plot_w = width - left - right
    plot_h = height - top - bottom

    if not pts:
        output_path.write_text(
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}"><text x="50%" y="50%">No plot data</text></svg>',
            encoding="utf-8",
        )
        return output_path

    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]

    xmin = 0
    xmax = max(xs)
    ymin = min(ys)
    ymax = max(ys)

    if xmax == xmin:
        xmax = 1

    if ymax == ymin:
        ymax = ymin + 0.1

    y_pad = (ymax - ymin) * 0.04
    ymin = ymin - y_pad
    ymax = ymax + y_pad

    def sx(x):
        return left + ((x - xmin) / (xmax - xmin)) * plot_w

    def sy(y):
        return top + ((y - ymin) / (ymax - ymin)) * plot_h

    grid = []
    labels = []

    step = _tick_step(xmax)
    tick_max = int(math.ceil(xmax / step) * step)

    for val in range(0, tick_max + 1, step):
        if val > xmax:
            continue

        x = sx(val)
        grid.append(
            f'<line x1="{x:.2f}" y1="{top}" x2="{x:.2f}" y2="{top + plot_h}" stroke="#cfcfcf" stroke-width="1"/>'
        )
        labels.append(
            f'<text x="{x:.2f}" y="{top - 13}" text-anchor="middle" font-family="Arial" font-size="15">{val}</text>'
        )

    for i in range(7):
        val = ymin + (ymax - ymin) * i / 6
        y = sy(val)

        grid.append(
            f'<line x1="{left}" y1="{y:.2f}" x2="{left + plot_w}" y2="{y:.2f}" stroke="#cfcfcf" stroke-width="1"/>'
        )
        labels.append(
            f'<text x="{left - 10}" y="{y + 5:.2f}" text-anchor="end" font-family="Arial" font-size="15">{val:.3f}</text>'
        )

    poly = " ".join(
        f"{sx(t):.2f},{sy(d):.2f}"
        for t, d in pts
    )

    circles = "\n".join(
        f'<circle cx="{sx(t):.2f}" cy="{sy(d):.2f}" r="3.8" fill="#003f23"/>'
        for t, d in pts
    )

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}">
<rect width="100%" height="100%" fill="white"/>
<rect x="{left}" y="{top}" width="{plot_w}" height="{plot_h}" fill="white" stroke="#333" stroke-width="1.2"/>
{"".join(grid)}
<polyline fill="none" stroke="#003f23" stroke-width="3" points="{poly}"/>
{circles}
{"".join(labels)}
<text x="{left + plot_w / 2}" y="{top - 32}" text-anchor="middle" font-family="Arial" font-size="17">Time (min)</text>
<text x="26" y="{top + plot_h / 2}" transform="rotate(-90 26 {top + plot_h / 2})" text-anchor="middle" font-family="Arial" font-size="17">Depth (mbgl)</text>
</svg>'''

    output_path.write_text(svg, encoding="utf-8")
    return output_path
