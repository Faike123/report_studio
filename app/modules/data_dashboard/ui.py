from __future__ import annotations

from collections import defaultdict
import math

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st


def _f(value, default=None):
    try:
        if value in (None, ""):
            return default
        return float(value)
    except Exception:
        return default


def _project_id(parsed: dict) -> str:
    groups = parsed.get("groups", {})
    proj = groups.get("PROJ", [])
    loca = groups.get("LOCA", [])

    if proj and proj[0].get("PROJ_ID"):
        return str(proj[0].get("PROJ_ID"))

    if loca and loca[0].get("PROJ_ID"):
        return str(loca[0].get("PROJ_ID"))

    return str(parsed.get("name", "unknown_project")).replace(".ags", "")


def _all_rows(ags_files: list[dict], group: str) -> list[dict]:
    out = []

    for parsed in ags_files:
        project_id = _project_id(parsed)
        file_name = parsed.get("name", "")

        for row in parsed.get("groups", {}).get(group, []) or []:
            item = dict(row)
            item["_PROJECT_ID"] = project_id
            item["_FILE"] = file_name
            out.append(item)

    return out


def _group_count_table(ags_files: list[dict]) -> pd.DataFrame:
    rows = []

    for parsed in ags_files:
        project_id = _project_id(parsed)
        file_name = parsed.get("name", "")
        groups = parsed.get("groups", {})

        for group, data_rows in sorted(groups.items()):
            rows.append({
                "project_id": project_id,
                "file": file_name,
                "group": group,
                "rows": len(data_rows),
                "columns": len(parsed.get("headings", {}).get(group, [])),
            })

    return pd.DataFrame(rows)


def _locations_df(ags_files: list[dict]) -> pd.DataFrame:
    rows = _all_rows(ags_files, "LOCA")

    out = []
    for r in rows:
        out.append({
            "project_id": r.get("_PROJECT_ID", ""),
            "file": r.get("_FILE", ""),
            "location_id": r.get("LOCA_ID", ""),
            "type": r.get("LOCA_TYPE", ""),
            "easting": _f(r.get("LOCA_NATE") or r.get("LOCA_LOCX")),
            "northing": _f(r.get("LOCA_NATN") or r.get("LOCA_LOCY")),
            "ground_level": _f(r.get("LOCA_GL") or r.get("LOCA_LOCZ")),
            "final_depth": _f(r.get("LOCA_FDEP")),
            "method": r.get("LOCA_METH", ""),
        })

    return pd.DataFrame(out)


def _geology_df(ags_files: list[dict]) -> pd.DataFrame:
    rows = _all_rows(ags_files, "GEOL")

    out = []
    for r in rows:
        top = _f(r.get("GEOL_TOP"))
        base = _f(r.get("GEOL_BASE"))
        thickness = None

        if top is not None and base is not None:
            thickness = max(0, base - top)

        material = r.get("GEOL_GEOL") or r.get("GEOL_LEG") or "UNKNOWN"

        out.append({
            "project_id": r.get("_PROJECT_ID", ""),
            "file": r.get("_FILE", ""),
            "location_id": r.get("LOCA_ID", ""),
            "top": top,
            "base": base,
            "thickness": thickness,
            "material": material,
            "description": r.get("GEOL_DESC") or r.get("GEOL_DESD") or r.get("GEOL_REM") or "",
        })

    return pd.DataFrame(out)


def _samples_df(ags_files: list[dict]) -> pd.DataFrame:
    rows = _all_rows(ags_files, "SAMP")

    out = []
    for r in rows:
        top = _f(r.get("SAMP_TOP"))
        base = _f(r.get("SAMP_BASE"))
        thickness = None

        if top is not None and base is not None:
            thickness = max(0, base - top)

        out.append({
            "project_id": r.get("_PROJECT_ID", ""),
            "file": r.get("_FILE", ""),
            "location_id": r.get("LOCA_ID", ""),
            "sample_id": r.get("SAMP_ID", ""),
            "sample_ref": r.get("SAMP_REF", ""),
            "type": r.get("SAMP_TYPE", ""),
            "top": top,
            "base": base,
            "thickness": thickness,
        })

    return pd.DataFrame(out)


def _spt_df(ags_files: list[dict]) -> pd.DataFrame:
    rows = _all_rows(ags_files, "ISPT")

    out = []
    for r in rows:
        nval = _f(r.get("ISPT_NVAL"))
        depth = _f(r.get("ISPT_TOP") or r.get("ISPT_DPTH"))

        out.append({
            "project_id": r.get("_PROJECT_ID", ""),
            "file": r.get("_FILE", ""),
            "location_id": r.get("LOCA_ID", ""),
            "depth": depth,
            "n_value": nval,
            "main": r.get("ISPT_MAIN", ""),
            "reported": r.get("ISPT_REP", ""),
        })

    return pd.DataFrame(out)


def _water_df(ags_files: list[dict]) -> pd.DataFrame:
    rows = _all_rows(ags_files, "WSTD") + _all_rows(ags_files, "WSTG")

    out = []
    for r in rows:
        depth = _f(r.get("WSTD_DPTH") or r.get("WSTG_DPTH"))
        out.append({
            "project_id": r.get("_PROJECT_ID", ""),
            "file": r.get("_FILE", ""),
            "location_id": r.get("LOCA_ID", ""),
            "depth": depth,
            "date": r.get("WSTD_DATE") or r.get("WSTG_DATE") or "",
            "remark": r.get("WSTD_REM") or r.get("WSTG_REM") or "",
        })

    return pd.DataFrame(out)


def _dcp_df(ags_files: list[dict]) -> pd.DataFrame:
    rows = _all_rows(ags_files, "DCPT")

    out = []
    for r in rows:
        out.append({
            "project_id": r.get("_PROJECT_ID", ""),
            "file": r.get("_FILE", ""),
            "location_id": r.get("LOCA_ID", ""),
            "run": r.get("DCPG_RUN", ""),
            "blow": _f(r.get("DCPT_BLOW")),
            "penetration_mm": _f(r.get("DCPT_PEN")),
            "depth": _f(r.get("DCPT_DPTH")),
            "mm_blow": _f(r.get("DCPT_MM_BLOW")),
            "icbr_est": _f(r.get("DCPT_ICBR_EST")),
        })

    return pd.DataFrame(out)


def _icbr_df(ags_files: list[dict]) -> pd.DataFrame:
    rows = _all_rows(ags_files, "ICBR")

    out = []
    for r in rows:
        top = _f(r.get("ICBR_FROM"))
        base = _f(r.get("ICBR_TO"))
        thickness = None

        if top is not None and base is not None:
            thickness = max(0, base - top)

        out.append({
            "project_id": r.get("_PROJECT_ID", ""),
            "file": r.get("_FILE", ""),
            "location_id": r.get("LOCA_ID", ""),
            "icbr_id": r.get("ICBR_ID", ""),
            "from_m": top,
            "to_m": base,
            "thickness": thickness,
            "cbr": _f(r.get("ICBR_CBR")),
            "method": r.get("ICBR_METH", ""),
            "description": r.get("ICBR_DESC", ""),
            "source": r.get("ICBR_SOURCE", ""),
        })

    return pd.DataFrame(out)


def _soakaway_df(ags_files: list[dict]) -> tuple[pd.DataFrame, pd.DataFrame]:
    isag_rows = _all_rows(ags_files, "ISAG")
    isat_rows = _all_rows(ags_files, "ISAT")

    general = []
    for r in isag_rows:
        general.append({
            "project_id": r.get("_PROJECT_ID", ""),
            "file": r.get("_FILE", ""),
            "location_id": r.get("LOCA_ID", ""),
            "run": r.get("ISAG_RUN", ""),
            "date": r.get("ISAG_DATE", ""),
            "length_m": _f(r.get("ISAG_LENGTH")),
            "width_m": _f(r.get("ISAG_WIDTH")),
            "depth_m": _f(r.get("ISAG_DEPTH")),
            "result_f": _f(r.get("ISAG_RESULT_F")),
            "method": r.get("ISAG_METHOD", ""),
            "weather": r.get("ISAG_WEATHER", ""),
        })

    readings = []
    for r in isat_rows:
        readings.append({
            "project_id": r.get("_PROJECT_ID", ""),
            "file": r.get("_FILE", ""),
            "location_id": r.get("LOCA_ID", ""),
            "run": r.get("ISAG_RUN", ""),
            "time_min": _f(r.get("ISAT_TIME")),
            "depth": _f(r.get("ISAT_DPTH")),
        })

    return pd.DataFrame(general), pd.DataFrame(readings)


def _core_df(ags_files: list[dict]) -> pd.DataFrame:
    rows = _all_rows(ags_files, "CORE")

    out = []
    for r in rows:
        top = _f(r.get("CORE_TOP"))
        base = _f(r.get("CORE_BASE"))
        thickness = None

        if top is not None and base is not None:
            thickness = max(0, base - top)

        out.append({
            "project_id": r.get("_PROJECT_ID", ""),
            "file": r.get("_FILE", ""),
            "location_id": r.get("LOCA_ID", ""),
            "top": top,
            "base": base,
            "thickness": thickness,
            "tcr": _f(r.get("CORE_PREC") or r.get("CORE_TCR")),
            "scr": _f(r.get("CORE_SREC") or r.get("CORE_SCR")),
            "rqd": _f(r.get("CORE_RQD")),
        })

    return pd.DataFrame(out)


def _fracture_df(ags_files: list[dict]) -> pd.DataFrame:
    rows = _all_rows(ags_files, "FRAC") + _all_rows(ags_files, "FRCT")

    out = []
    for r in rows:
        out.append({
            "project_id": r.get("_PROJECT_ID", ""),
            "file": r.get("_FILE", ""),
            "location_id": r.get("LOCA_ID", ""),
            "depth": _f(r.get("FRAC_DPTH") or r.get("FRCT_DPTH")),
            "type": r.get("FRAC_TYPE") or r.get("FRCT_TYPE") or "",
            "description": r.get("FRAC_DESC") or r.get("FRCT_DESC") or "",
        })

    return pd.DataFrame(out)


def _vane_df(ags_files: list[dict]) -> pd.DataFrame:
    rows = _all_rows(ags_files, "IVAN")

    out = []
    for r in rows:
        out.append({
            "project_id": r.get("_PROJECT_ID", ""),
            "file": r.get("_FILE", ""),
            "location_id": r.get("LOCA_ID", ""),
            "depth": _f(r.get("IVAN_DPTH")),
            "test_no": r.get("IVAN_TESN", ""),
            "type": r.get("IVAN_TYPE", ""),
            "undrained_shear_kpa": _f(r.get("IVAN_IVAN")),
            "residual_kpa": _f(r.get("IVAN_IVAR")),
            "date": r.get("IVAN_DATE", ""),
        })

    return pd.DataFrame(out)


def _pid_df(ags_files: list[dict]) -> pd.DataFrame:
    rows = _all_rows(ags_files, "IPID")

    out = []
    for r in rows:
        out.append({
            "project_id": r.get("_PROJECT_ID", ""),
            "file": r.get("_FILE", ""),
            "location_id": r.get("LOCA_ID", ""),
            "depth": _f(r.get("IPID_DPTH")),
            "pid": _f(r.get("IPID_RESL")),
            "unit": r.get("IPID_UNIT", ""),
            "date": r.get("IPID_DATE", ""),
        })

    return pd.DataFrame(out)


def _eres_df(ags_files: list[dict]) -> pd.DataFrame:
    rows = _all_rows(ags_files, "ERES")

    out = []
    for r in rows:
        top = _f(r.get("ERES_TOP"))
        base = _f(r.get("ERES_BASE"))
        thickness = None

        if top is not None and base is not None:
            thickness = max(0, base - top)

        out.append({
            "project_id": r.get("_PROJECT_ID", ""),
            "file": r.get("_FILE", ""),
            "location_id": r.get("LOCA_ID", ""),
            "top": top,
            "base": base,
            "thickness": thickness,
            "resistivity": _f(r.get("ERES_RESL")),
            "unit": r.get("ERES_UNIT", ""),
        })

    return pd.DataFrame(out)


def _filter_projects(df: pd.DataFrame, selected_projects: list[str]) -> pd.DataFrame:
    if df.empty:
        return df

    if not selected_projects or "All" in selected_projects:
        return df

    if "project_id" not in df.columns:
        return df

    return df[df["project_id"].isin(selected_projects)].copy()


def _safe_plotly_chart(fig, key: str):
    fig.update_layout(
        margin=dict(l=40, r=20, t=45, b=35),
        paper_bgcolor="white",
        plot_bgcolor="white",
        font=dict(size=12),
    )
    st.plotly_chart(fig, use_container_width=True, key=key)


def _empty_msg(name: str):
    st.info(f"No {name} data detected in loaded AGS files.")


def render_data_dashboard_page():
    st.header("Data Dashboard")
    st.caption("Visual summaries of all loaded AGS data: geology thicknesses, test distributions, depth profiles, samples, water, rock quality, DCP, ICBR, soakaway, PID, vane and ERES.")

    ags_files = st.session_state.get("ags_files", [])

    if not ags_files:
        st.warning("No AGS files loaded yet. Import AGS or mixed ZIP data first.")
        return

    group_counts = _group_count_table(ags_files)
    locations = _locations_df(ags_files)

    geology = _geology_df(ags_files)
    samples = _samples_df(ags_files)
    spt = _spt_df(ags_files)
    water = _water_df(ags_files)
    dcp = _dcp_df(ags_files)
    icbr = _icbr_df(ags_files)
    soak_general, soak_readings = _soakaway_df(ags_files)
    core = _core_df(ags_files)
    fractures = _fracture_df(ags_files)
    vane = _vane_df(ags_files)
    pid = _pid_df(ags_files)
    eres = _eres_df(ags_files)

    projects = sorted(group_counts["project_id"].dropna().unique().tolist()) if not group_counts.empty else []
    selected_projects = st.multiselect(
        "Project filter",
        ["All"] + projects,
        default=["All"],
    )

    group_counts = _filter_projects(group_counts, selected_projects)
    locations = _filter_projects(locations, selected_projects)
    geology = _filter_projects(geology, selected_projects)
    samples = _filter_projects(samples, selected_projects)
    spt = _filter_projects(spt, selected_projects)
    water = _filter_projects(water, selected_projects)
    dcp = _filter_projects(dcp, selected_projects)
    icbr = _filter_projects(icbr, selected_projects)
    soak_general = _filter_projects(soak_general, selected_projects)
    soak_readings = _filter_projects(soak_readings, selected_projects)
    core = _filter_projects(core, selected_projects)
    fractures = _filter_projects(fractures, selected_projects)
    vane = _filter_projects(vane, selected_projects)
    pid = _filter_projects(pid, selected_projects)
    eres = _filter_projects(eres, selected_projects)

    st.subheader("Overview")

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("AGS files", len(ags_files))
    c2.metric("Projects", len(projects))
    c3.metric("Locations", len(locations))
    c4.metric("Groups", len(group_counts))
    c5.metric("Data rows", int(group_counts["rows"].sum()) if not group_counts.empty else 0)

    overview_tabs = st.tabs([
        "Group Coverage",
        "Locations",
        "Geology",
        "Samples",
        "Tests",
        "Hydro",
        "Rock",
        "DCP / CBR",
        "Soakaway",
        "Environmental",
        "Raw Data",
    ])

    with overview_tabs[0]:
        _render_group_coverage(group_counts, locations)

    with overview_tabs[1]:
        _render_locations(locations)

    with overview_tabs[2]:
        _render_geology(geology, locations)

    with overview_tabs[3]:
        _render_samples(samples)

    with overview_tabs[4]:
        _render_tests(spt, vane)

    with overview_tabs[5]:
        _render_hydro(water)

    with overview_tabs[6]:
        _render_rock(core, fractures)

    with overview_tabs[7]:
        _render_dcp_cbr(dcp, icbr)

    with overview_tabs[8]:
        _render_soakaway(soak_general, soak_readings)

    with overview_tabs[9]:
        _render_environmental(pid, eres)

    with overview_tabs[10]:
        _render_raw_tables({
            "Locations": locations,
            "Geology": geology,
            "Samples": samples,
            "SPT": spt,
            "Water": water,
            "Core": core,
            "Fractures": fractures,
            "DCP": dcp,
            "ICBR": icbr,
            "Soakaway General": soak_general,
            "Soakaway Readings": soak_readings,
            "Hand Vane": vane,
            "PID": pid,
            "ERES": eres,
        })


def _render_group_coverage(group_counts: pd.DataFrame, locations: pd.DataFrame):
    if group_counts.empty:
        _empty_msg("group coverage")
        return

    c1, c2 = st.columns([1, 1])

    with c1:
        by_group = group_counts.groupby("group", as_index=False)["rows"].sum().sort_values("rows", ascending=False)
        fig = px.bar(by_group, x="group", y="rows", title="Rows by AGS Group")
        _safe_plotly_chart(fig, "dash_group_rows")

    with c2:
        by_project = group_counts.groupby("project_id", as_index=False)["rows"].sum().sort_values("rows", ascending=False)
        fig = px.bar(by_project, x="project_id", y="rows", title="Rows by Project")
        _safe_plotly_chart(fig, "dash_project_rows")

    st.write("Group inventory")
    st.dataframe(group_counts.sort_values(["project_id", "group"]), use_container_width=True)

    if not locations.empty and "type" in locations.columns:
        loc_type = locations.groupby("type", as_index=False).size().rename(columns={"size": "locations"})
        fig = px.pie(loc_type, names="type", values="locations", title="Location Type Mix")
        _safe_plotly_chart(fig, "dash_location_type_pie")


def _render_locations(locations: pd.DataFrame):
    if locations.empty:
        _empty_msg("location")
        return

    c1, c2 = st.columns([1, 1])

    with c1:
        if {"easting", "northing"}.issubset(locations.columns):
            map_df = locations.dropna(subset=["easting", "northing"]).copy()
            if not map_df.empty:
                fig = px.scatter(
                    map_df,
                    x="easting",
                    y="northing",
                    color="type",
                    hover_name="location_id",
                    size="final_depth",
                    title="Location Plan View",
                )
                fig.update_yaxes(scaleanchor="x", scaleratio=1)
                _safe_plotly_chart(fig, "dash_location_plan")
            else:
                st.info("No coordinates available.")

    with c2:
        depth_df = locations.dropna(subset=["final_depth"]).copy()
        if not depth_df.empty:
            fig = px.histogram(depth_df, x="final_depth", color="type", nbins=16, title="Final Depth Distribution")
            _safe_plotly_chart(fig, "dash_final_depth_hist")

    c3, c4 = st.columns([1, 1])

    with c3:
        depth_by_type = locations.groupby("type", as_index=False)["final_depth"].sum().sort_values("final_depth", ascending=False)
        fig = px.bar(depth_by_type, x="type", y="final_depth", title="Total Drilled / Excavated Depth by Location Type")
        _safe_plotly_chart(fig, "dash_total_depth_type")

    with c4:
        count_by_project = locations.groupby(["project_id", "type"], as_index=False).size().rename(columns={"size": "locations"})
        fig = px.bar(count_by_project, x="project_id", y="locations", color="type", title="Locations by Project and Type")
        _safe_plotly_chart(fig, "dash_location_project_type")

    st.dataframe(locations, use_container_width=True)


def _render_geology(geology: pd.DataFrame, locations: pd.DataFrame):
    if geology.empty:
        _empty_msg("geology")
        return

    c1, c2 = st.columns([1, 1])

    with c1:
        mat = geology.groupby("material", as_index=False)["thickness"].sum().sort_values("thickness", ascending=False)
        fig = px.bar(mat, x="material", y="thickness", title="Total Geology Thickness by Material")
        _safe_plotly_chart(fig, "dash_geol_material_thickness")

    with c2:
        mat_count = geology.groupby("material", as_index=False).size().rename(columns={"size": "intervals"}).sort_values("intervals", ascending=False)
        fig = px.bar(mat_count, x="material", y="intervals", title="Geology Interval Count by Material")
        _safe_plotly_chart(fig, "dash_geol_material_count")

    c3, c4 = st.columns([1, 1])

    with c3:
        loc_mat = geology.groupby(["location_id", "material"], as_index=False)["thickness"].sum()
        fig = px.bar(loc_mat, x="location_id", y="thickness", color="material", title="Geology Thickness by Location")
        _safe_plotly_chart(fig, "dash_geol_location_stack")

    with c4:
        top_df = geology.dropna(subset=["top"]).copy()
        if not top_df.empty:
            fig = px.box(top_df, x="material", y="top", title="Depth Range by Material")
            fig.update_yaxes(autorange="reversed")
            _safe_plotly_chart(fig, "dash_geol_depth_box")

    st.subheader("Geology Profile Viewer")
    locs = sorted(geology["location_id"].dropna().unique().tolist())
    selected_loc = st.selectbox("Select location for geology strip", locs, key="dash_geol_profile_loc")

    gdf = geology[geology["location_id"] == selected_loc].copy()
    fig = go.Figure()

    for _, row in gdf.iterrows():
        top = row["top"]
        base = row["base"]
        if pd.isna(top) or pd.isna(base):
            continue

        fig.add_trace(
            go.Bar(
                x=[1],
                y=[base - top],
                base=[top],
                orientation="v",
                name=str(row["material"]),
                text=[str(row["material"])],
                hovertext=[row["description"]],
                hoverinfo="text",
                width=0.55,
            )
        )

    fig.update_layout(
        title=f"Geology Column — {selected_loc}",
        xaxis=dict(showticklabels=False, title=""),
        yaxis=dict(title="Depth (m)", autorange="reversed"),
        barmode="stack",
        showlegend=True,
        height=650,
    )
    _safe_plotly_chart(fig, "dash_geol_single_profile")

    st.dataframe(geology.sort_values(["location_id", "top"]), use_container_width=True)


def _render_samples(samples: pd.DataFrame):
    if samples.empty:
        _empty_msg("sample")
        return

    c1, c2 = st.columns([1, 1])

    with c1:
        by_type = samples.groupby("type", as_index=False).size().rename(columns={"size": "samples"})
        fig = px.bar(by_type, x="type", y="samples", title="Samples by Type")
        _safe_plotly_chart(fig, "dash_samples_type")

    with c2:
        by_loc = samples.groupby(["location_id", "type"], as_index=False).size().rename(columns={"size": "samples"})
        fig = px.bar(by_loc, x="location_id", y="samples", color="type", title="Samples by Location")
        _safe_plotly_chart(fig, "dash_samples_location")

    depth_df = samples.dropna(subset=["top"]).copy()
    if not depth_df.empty:
        fig = px.scatter(
            depth_df,
            x="location_id",
            y="top",
            color="type",
            hover_data=["sample_id", "sample_ref", "base"],
            title="Sample Depths",
        )
        fig.update_yaxes(autorange="reversed", title="Depth (m)")
        _safe_plotly_chart(fig, "dash_sample_depths")

    st.dataframe(samples.sort_values(["location_id", "top"]), use_container_width=True)


def _render_tests(spt: pd.DataFrame, vane: pd.DataFrame):
    if spt.empty and vane.empty:
        _empty_msg("SPT / hand vane")
        return

    if not spt.empty:
        st.subheader("SPT")
        c1, c2 = st.columns([1, 1])

        with c1:
            fig = px.scatter(
                spt.dropna(subset=["depth", "n_value"]),
                x="n_value",
                y="depth",
                color="location_id",
                hover_data=["main", "reported"],
                title="SPT N-value vs Depth",
            )
            fig.update_yaxes(autorange="reversed", title="Depth (m)")
            _safe_plotly_chart(fig, "dash_spt_depth")

        with c2:
            fig = px.histogram(spt.dropna(subset=["n_value"]), x="n_value", nbins=15, title="SPT N-value Distribution")
            _safe_plotly_chart(fig, "dash_spt_hist")

        spt_summary = spt.groupby("location_id", as_index=False).agg(
            spt_count=("n_value", "count"),
            min_n=("n_value", "min"),
            mean_n=("n_value", "mean"),
            max_n=("n_value", "max"),
        )
        st.dataframe(spt_summary, use_container_width=True)

    if not vane.empty:
        st.subheader("Hand Vane")
        c1, c2 = st.columns([1, 1])

        with c1:
            fig = px.scatter(
                vane.dropna(subset=["depth", "undrained_shear_kpa"]),
                x="undrained_shear_kpa",
                y="depth",
                color="location_id",
                hover_data=["residual_kpa", "type"],
                title="Hand Vane Strength vs Depth",
            )
            fig.update_yaxes(autorange="reversed", title="Depth (m)")
            _safe_plotly_chart(fig, "dash_vane_depth")

        with c2:
            fig = px.box(
                vane.dropna(subset=["undrained_shear_kpa"]),
                x="location_id",
                y="undrained_shear_kpa",
                title="Hand Vane Strength by Location",
            )
            _safe_plotly_chart(fig, "dash_vane_box")

        st.dataframe(vane.sort_values(["location_id", "depth"]), use_container_width=True)


def _render_hydro(water: pd.DataFrame):
    if water.empty:
        _empty_msg("water")
        return

    c1, c2 = st.columns([1, 1])

    with c1:
        fig = px.scatter(
            water.dropna(subset=["depth"]),
            x="location_id",
            y="depth",
            hover_data=["date", "remark"],
            title="Water Observations by Depth",
        )
        fig.update_yaxes(autorange="reversed", title="Depth (m)")
        _safe_plotly_chart(fig, "dash_water_depth")

    with c2:
        fig = px.histogram(water.dropna(subset=["depth"]), x="depth", nbins=14, title="Water Depth Distribution")
        _safe_plotly_chart(fig, "dash_water_hist")

    st.dataframe(water.sort_values(["location_id", "depth"]), use_container_width=True)


def _render_rock(core: pd.DataFrame, fractures: pd.DataFrame):
    if core.empty and fractures.empty:
        _empty_msg("rock")
        return

    if not core.empty:
        st.subheader("Core Recovery / RQD")

        c1, c2 = st.columns([1, 1])

        with c1:
            long = core.melt(
                id_vars=["project_id", "location_id", "top", "base"],
                value_vars=[c for c in ["tcr", "scr", "rqd"] if c in core.columns],
                var_name="metric",
                value_name="percent",
            )
            fig = px.scatter(
                long.dropna(subset=["percent", "top"]),
                x="percent",
                y="top",
                color="metric",
                symbol="location_id",
                hover_data=["location_id", "base"],
                title="Core Quality Metrics vs Depth",
            )
            fig.update_yaxes(autorange="reversed", title="Depth (m)")
            _safe_plotly_chart(fig, "dash_core_quality_depth")

        with c2:
            summary = core.groupby("location_id", as_index=False).agg(
                mean_tcr=("tcr", "mean"),
                mean_scr=("scr", "mean"),
                mean_rqd=("rqd", "mean"),
                core_m=("thickness", "sum"),
            )
            fig = px.bar(
                summary,
                x="location_id",
                y=["mean_tcr", "mean_scr", "mean_rqd"],
                barmode="group",
                title="Mean Core Quality by Location",
            )
            _safe_plotly_chart(fig, "dash_core_quality_summary")

        st.dataframe(core.sort_values(["location_id", "top"]), use_container_width=True)

    if not fractures.empty:
        st.subheader("Fractures")

        c1, c2 = st.columns([1, 1])

        with c1:
            fig = px.scatter(
                fractures.dropna(subset=["depth"]),
                x="location_id",
                y="depth",
                color="type",
                hover_data=["description"],
                title="Fracture Depths",
            )
            fig.update_yaxes(autorange="reversed", title="Depth (m)")
            _safe_plotly_chart(fig, "dash_fractures_depth")

        with c2:
            counts = fractures.groupby(["location_id", "type"], as_index=False).size().rename(columns={"size": "fractures"})
            fig = px.bar(counts, x="location_id", y="fractures", color="type", title="Fractures by Location")
            _safe_plotly_chart(fig, "dash_fractures_count")

        st.dataframe(fractures.sort_values(["location_id", "depth"]), use_container_width=True)


def _render_dcp_cbr(dcp: pd.DataFrame, icbr: pd.DataFrame):
    if dcp.empty and icbr.empty:
        _empty_msg("DCP / ICBR")
        return

    if not dcp.empty:
        st.subheader("DCP")

        locs = sorted(dcp["location_id"].dropna().unique().tolist())
        selected = st.selectbox("DCP location", locs, key="dash_dcp_loc")

        one = dcp[dcp["location_id"] == selected].dropna(subset=["depth"]).copy()

        c1, c2 = st.columns([1, 1])

        with c1:
            fig = px.line(
                one.sort_values("depth"),
                x="blow",
                y="depth",
                markers=True,
                title=f"DCP Blows vs Depth — {selected}",
            )
            fig.update_yaxes(autorange="reversed", title="Depth (m)")
            _safe_plotly_chart(fig, "dash_dcp_blow_depth")

        with c2:
            fig = px.line(
                one.sort_values("depth"),
                x="icbr_est",
                y="depth",
                markers=True,
                title=f"Estimated ICBR vs Depth — {selected}",
            )
            fig.update_yaxes(autorange="reversed", title="Depth (m)")
            _safe_plotly_chart(fig, "dash_dcp_icbr_depth")

        dcp_summary = dcp.groupby("location_id", as_index=False).agg(
            max_depth=("depth", "max"),
            blows=("blow", "max"),
            min_icbr=("icbr_est", "min"),
            mean_icbr=("icbr_est", "mean"),
            max_icbr=("icbr_est", "max"),
        )
        st.dataframe(dcp_summary, use_container_width=True)

    if not icbr.empty:
        st.subheader("ICBR Layers")

        c1, c2 = st.columns([1, 1])

        with c1:
            fig = px.bar(
                icbr.dropna(subset=["cbr"]),
                x="location_id",
                y="cbr",
                color="description",
                hover_data=["from_m", "to_m", "method"],
                title="ICBR Layer Values",
            )
            _safe_plotly_chart(fig, "dash_icbr_values")

        with c2:
            fig = px.scatter(
                icbr.dropna(subset=["from_m", "cbr"]),
                x="cbr",
                y="from_m",
                color="location_id",
                hover_data=["to_m", "description"],
                title="ICBR vs Layer Depth",
            )
            fig.update_yaxes(autorange="reversed", title="Depth (m)")
            _safe_plotly_chart(fig, "dash_icbr_depth")

        st.dataframe(icbr.sort_values(["location_id", "from_m"]), use_container_width=True)


def _render_soakaway(general: pd.DataFrame, readings: pd.DataFrame):
    if general.empty and readings.empty:
        _empty_msg("soakaway")
        return

    if not general.empty:
        st.subheader("Soakaway General")

        c1, c2 = st.columns([1, 1])

        with c1:
            fig = px.bar(
                general.dropna(subset=["result_f"]),
                x="location_id",
                y="result_f",
                color="weather",
                title="Infiltration Rate by Location",
            )
            _safe_plotly_chart(fig, "dash_soak_f")

        with c2:
            dims = general.melt(
                id_vars=["location_id", "run"],
                value_vars=[c for c in ["length_m", "width_m", "depth_m"] if c in general.columns],
                var_name="dimension",
                value_name="metres",
            )
            fig = px.bar(dims, x="location_id", y="metres", color="dimension", barmode="group", title="Soakaway Pit Dimensions")
            _safe_plotly_chart(fig, "dash_soak_dims")

        st.dataframe(general, use_container_width=True)

    if not readings.empty:
        st.subheader("Soakaway Readings")

        locs = sorted(readings["location_id"].dropna().unique().tolist())
        selected = st.selectbox("Soakaway location", locs, key="dash_soak_loc")
        one = readings[readings["location_id"] == selected].copy()

        fig = px.line(
            one.sort_values("time_min"),
            x="time_min",
            y="depth",
            markers=True,
            title=f"Soakaway Depth vs Time — {selected}",
        )
        fig.update_yaxes(title="Depth mbgl")
        fig.update_xaxes(title="Time (min)")
        _safe_plotly_chart(fig, "dash_soak_curve")

        st.dataframe(readings.sort_values(["location_id", "time_min"]), use_container_width=True)


def _render_environmental(pid: pd.DataFrame, eres: pd.DataFrame):
    if pid.empty and eres.empty:
        _empty_msg("environmental / ERES")
        return

    if not pid.empty:
        st.subheader("PID")

        c1, c2 = st.columns([1, 1])

        with c1:
            fig = px.scatter(
                pid.dropna(subset=["depth", "pid"]),
                x="pid",
                y="depth",
                color="location_id",
                hover_data=["unit", "date"],
                title="PID vs Depth",
            )
            fig.update_yaxes(autorange="reversed", title="Depth (m)")
            _safe_plotly_chart(fig, "dash_pid_depth")

        with c2:
            fig = px.box(pid.dropna(subset=["pid"]), x="location_id", y="pid", title="PID by Location")
            _safe_plotly_chart(fig, "dash_pid_box")

        st.dataframe(pid.sort_values(["location_id", "depth"]), use_container_width=True)

    if not eres.empty:
        st.subheader("ERES")

        c1, c2 = st.columns([1, 1])

        with c1:
            fig = px.scatter(
                eres.dropna(subset=["top", "resistivity"]),
                x="resistivity",
                y="top",
                color="location_id",
                hover_data=["base", "unit"],
                title="Electrical Resistivity vs Depth",
            )
            fig.update_yaxes(autorange="reversed", title="Depth (m)")
            _safe_plotly_chart(fig, "dash_eres_depth")

        with c2:
            summary = eres.groupby("location_id", as_index=False).agg(
                mean_resistivity=("resistivity", "mean"),
                min_resistivity=("resistivity", "min"),
                max_resistivity=("resistivity", "max"),
            )
            fig = px.bar(summary, x="location_id", y="mean_resistivity", title="Mean ERES by Location")
            _safe_plotly_chart(fig, "dash_eres_summary")

        st.dataframe(eres.sort_values(["location_id", "top"]), use_container_width=True)


def _render_raw_tables(tables: dict[str, pd.DataFrame]):
    names = list(tables.keys())
    selected = st.selectbox("Table", names, key="dash_raw_table")

    df = tables[selected]

    if df.empty:
        st.info(f"No data in {selected}.")
    else:
        st.dataframe(df, use_container_width=True)
