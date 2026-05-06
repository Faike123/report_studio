from __future__ import annotations

import plotly.graph_objects as go

from app.modules.dcp.layers import dcp_points


def make_dcp_plotly_figure(dcp_test: dict, layer_rows: list[dict] | None = None):
    points = dcp_points(dcp_test)

    x = []
    y = []
    custom = []

    for p in points:
        blow = p.get("blow")
        depth = p.get("depth_m")

        if blow is None or depth is None:
            continue

        x.append(blow)
        y.append(depth)
        custom.append([
            depth,
            p.get("icbr"),
            p.get("penetration_mm"),
            p.get("mm_blow"),
        ])

    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=x,
            y=y,
            mode="lines+markers",
            name="DCP",
            customdata=custom,
            marker=dict(size=9),
            line=dict(width=2),
            hovertemplate=(
                "Blows: %{x}<br>"
                "Depth: %{y:.3f} m<br>"
                "ICBR: %{customdata[1]:.2f}%<br>"
                "Penetration: %{customdata[2]:.1f} mm<br>"
                "mm/blow: %{customdata[3]:.2f}"
                "<extra></extra>"
            ),
        )
    )

    if layer_rows:
        for layer in layer_rows:
            try:
                from_m = float(layer.get("from_m", 0))
                to_m = float(layer.get("to_m", 0))
            except Exception:
                continue

            if to_m <= from_m:
                continue

            fig.add_hrect(
                y0=from_m,
                y1=to_m,
                line_width=0,
                opacity=0.08,
            )

            fig.add_hline(
                y=from_m,
                line_width=1,
                line_dash="dot",
                line_color="gray",
            )

            fig.add_hline(
                y=to_m,
                line_width=1,
                line_dash="dot",
                line_color="gray",
            )

    fig.update_yaxes(
        autorange="reversed",
        title="Depth (m)",
        gridcolor="lightgray",
        zeroline=True,
    )

    fig.update_xaxes(
        title="Blows",
        side="top",
        gridcolor="lightgray",
        rangemode="tozero",
    )

    fig.update_layout(
        height=650,
        margin=dict(l=60, r=40, t=70, b=30),
        showlegend=False,
        clickmode="event+select",
        dragmode=False,
    )

    return fig
