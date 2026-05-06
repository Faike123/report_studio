from __future__ import annotations

from collections import defaultdict

import pandas as pd
import streamlit as st


def _project_id(parsed: dict) -> str:
    groups = parsed.get("groups", {})
    proj = groups.get("PROJ", [])
    loca = groups.get("LOCA", [])

    if proj and proj[0].get("PROJ_ID"):
        return str(proj[0].get("PROJ_ID"))

    if loca and loca[0].get("PROJ_ID"):
        return str(loca[0].get("PROJ_ID"))

    return str(parsed.get("name", "unknown_project")).replace(".ags", "")


def _loca_ids(rows: list[dict]) -> list[str]:
    return sorted({
        str(row.get("LOCA_ID", "")).strip()
        for row in rows
        if str(row.get("LOCA_ID", "")).strip()
    })


def render_data_inventory_page():
    st.header("Data Inventory")
    st.caption("Scans every loaded AGS group, including data that does not yet have a PDF reporting engine.")

    ags_files = st.session_state.get("ags_files", [])

    if not ags_files:
        st.warning("No AGS files loaded yet. Import AGS or mixed ZIP data first.")
        return

    inventory_rows = []
    location_rows = []

    for file_index, parsed in enumerate(ags_files):
        project_id = _project_id(parsed)
        groups = parsed.get("groups", {})
        headings = parsed.get("headings", {})

        for group, rows in sorted(groups.items()):
            locs = _loca_ids(rows)

            inventory_rows.append({
                "file_index": file_index,
                "file": parsed.get("name", ""),
                "project_id": project_id,
                "group": group,
                "rows": len(rows),
                "columns": len(headings.get(group, [])),
                "locations": len(locs),
                "location_list": ", ".join(locs[:12]) + ("..." if len(locs) > 12 else ""),
                "has_loca_id": "Yes" if locs else "",
            })

            by_loca = defaultdict(int)
            for row in rows:
                loca_id = str(row.get("LOCA_ID", "")).strip()
                if loca_id:
                    by_loca[loca_id] += 1

            for loca_id, count in sorted(by_loca.items()):
                location_rows.append({
                    "file_index": file_index,
                    "project_id": project_id,
                    "location_id": loca_id,
                    "group": group,
                    "rows": count,
                })

    st.subheader("Group Inventory")
    df = pd.DataFrame(inventory_rows)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("AGS files", len(ags_files))
    c2.metric("Groups detected", len(df))
    c3.metric("Rows detected", int(df["rows"].sum()) if not df.empty else 0)
    c4.metric("Location-linked groups", int((df["has_loca_id"] == "Yes").sum()) if not df.empty else 0)

    group_filter = st.multiselect(
        "Filter groups",
        sorted(df["group"].unique().tolist()) if not df.empty else [],
        default=[],
    )

    shown = df.copy()
    if group_filter:
        shown = shown[shown["group"].isin(group_filter)]

    st.dataframe(shown, use_container_width=True)

    st.subheader("Location x Group Matrix")

    loc_df = pd.DataFrame(location_rows)

    if loc_df.empty:
        st.info("No location-linked group rows found.")
        return

    pivot = (
        loc_df
        .pivot_table(
            index=["project_id", "location_id"],
            columns="group",
            values="rows",
            aggfunc="sum",
            fill_value=0,
        )
        .reset_index()
    )

    st.dataframe(pivot, use_container_width=True)

    st.subheader("Raw Group Preview")

    selected_file = st.selectbox(
        "AGS file",
        options=list(range(len(ags_files))),
        format_func=lambda i: f"{i}: {ags_files[i].get('name', '')}",
    )

    groups = sorted(ags_files[selected_file].get("groups", {}).keys())

    selected_group = st.selectbox("Group", groups)

    rows = ags_files[selected_file].get("groups", {}).get(selected_group, [])

    st.write(f"Previewing `{selected_group}` — {len(rows)} rows")
    st.dataframe(pd.DataFrame(rows), use_container_width=True)
