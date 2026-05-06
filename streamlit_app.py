from __future__ import annotations

from pathlib import Path
import shutil
from collections import defaultdict
import zipfile

import pandas as pd
import streamlit as st
from app.ui.igne_theme import apply_igne_theme, hero
from streamlit_plotly_events import plotly_events

from app.core.file_router import classify_file
from app.core.zip_parser import parse_flowfinity_zip, location_summary
from app.core.pdf_merge import merge_pdfs
from app.core.ags_parser import parse_ags_file, ags_summary

from app.modules.borehole.from_ags import borehole_reports_from_ags
from app.modules.borehole.service import export_pdf as export_borehole_pdf
from app.modules.borehole.strip_registry import default_strip_layout, registry_rows, categories
from app.modules.full_report.service import export_full_ags_report
from app.modules.report_builder.ui import render_report_builder_page

from app.modules.soakaway.from_xlsx import parse_soakaway_xlsx
from app.modules.soakaway.from_ags_csv import reports_from_flowfinity
from app.modules.soakaway.service import export_pdf as export_soakaway_pdf
from app.modules.soakaway.ags_export import export_soakaway_ags_zip_by_project
from app.modules.soakaway.ags_file_export import export_soakaway_ags_file_by_project

from app.modules.dcp.from_ags_csv import dcp_tests_from_flowfinity
from app.modules.dcp.layers import (
    default_layers_for_dcp,
    calculate_layer_icbr,
    icbr_rows_from_layers,
    layers_from_break_depths,
)
from app.modules.dcp.dashboard import make_dcp_plotly_figure
from app.modules.dcp.dashboard import make_dcp_plotly_figure
from app.modules.dcp.service import export_pdf as export_dcp_pdf
from app.modules.dcp.ags_export import export_dcp_ags_zip_by_project
from app.modules.dcp.ags_file_export import export_dcp_ags_file_by_project


ROOT = Path(__file__).resolve().parent
TEMP = ROOT / "temp"
OUTPUT = ROOT / "output"

TEMP.mkdir(exist_ok=True)
OUTPUT.mkdir(exist_ok=True)

st.set_page_config(
    page_title="Report Studio",
    page_icon="🟩",
    layout="wide",
    initial_sidebar_state="expanded",
)

apply_igne_theme()


defaults = {
    "loaded_files": [],
    "parsed_zips": [],
    "soakaway_reports": [],
    "dcp_tests": [],
    "import_summary": [],
    "soakaway_downloads": {},
    "soakaway_ags_downloads": {},
    "soakaway_ags_file_downloads": {},
    "dcp_downloads": {},
    "dcp_ags_downloads": {},
    "dcp_ags_file_downloads": {},
    "dcp_layer_store": {},
    "ags_files": [],
    "borehole_reports": [],
    "borehole_downloads": {},
    "borehole_strip_layout": [],
    "full_report_downloads": {},
    "report_builder_items": [],
    "report_builder_current_index": 0,
    "report_builder_outputs": {},
    "report_builder_stage": "detect",
    "ags_files": [],
    "borehole_reports": [],
    "borehole_downloads": {},
}

for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value


def save_upload(file) -> Path:
    path = TEMP / file.name
    with open(path, "wb") as f:
        f.write(file.getbuffer())
    return path


def reset_project_store():
    for key, value in defaults.items():
        st.session_state[key] = value.copy() if isinstance(value, dict) else []


def load_files_into_project_store(files):
    reset_project_store()

    work = TEMP / "project_store"
    if work.exists():
        shutil.rmtree(work)
    work.mkdir(parents=True, exist_ok=True)

    loaded_files = []
    parsed_zips = []
    soakaway_reports = []
    dcp_tests = []
    import_summary = []

    for file in files:
        path = save_upload(file)
        kind = classify_file(path)

        loaded_files.append({
            "file": file.name,
            "classification": kind,
            "path": str(path),
        })

        if kind == "ags_file":
            parsed_ags = parse_ags_file(path)
            st.session_state.ags_files.append(parsed_ags)

            new_boreholes = borehole_reports_from_ags(parsed_ags)
            st.session_state.borehole_reports.extend(new_boreholes)

            import_summary.append({
                "file": file.name,
                "type": kind,
                "locations": len(new_boreholes),
                "groups": ", ".join(g["group"] for g in ags_summary(parsed_ags)),
                "soakaway_tests": 0,
                "dcp_tests": 0,
                "borehole_logs": len(new_boreholes),
            })

        elif kind in ("multi_test_ags_csv_zip", "soakaway_ags_csv_zip", "dcp_ags_csv_zip", "ags_csv_zip"):
            parsed = parse_flowfinity_zip(path)
            parsed_zips.append(parsed)

            new_soakaways = reports_from_flowfinity(parsed)
            new_dcps = dcp_tests_from_flowfinity(parsed)

            soakaway_reports.extend(new_soakaways)
            dcp_tests.extend(new_dcps)

            import_summary.append({
                "file": file.name,
                "type": kind,
                "locations": len(parsed["locations"]),
                "groups": ", ".join(parsed["groups_present"]),
                "soakaway_tests": len(new_soakaways),
                "dcp_tests": len(new_dcps),
            })

        elif path.suffix.lower() == ".zip":
            extract_dir = work / path.stem
            extract_dir.mkdir(parents=True, exist_ok=True)

            with zipfile.ZipFile(path, "r") as z:
                z.extractall(extract_dir)

            xlsx_files = list(extract_dir.rglob("*.xlsx"))
            ags_files = list(extract_dir.rglob("*.ags"))

            for xlsx in xlsx_files:
                if "soakaway" in xlsx.name.lower():
                    soakaway_reports.append(parse_soakaway_xlsx(xlsx))

            bh_count = 0
            for ags in ags_files:
                parsed_ags = parse_ags_file(ags)
                st.session_state.ags_files.append(parsed_ags)
                new_boreholes = borehole_reports_from_ags(parsed_ags)
                st.session_state.borehole_reports.extend(new_boreholes)
                bh_count += len(new_boreholes)

            import_summary.append({
                "file": file.name,
                "type": kind,
                "locations": bh_count,
                "groups": "XLSX / AGS",
                "soakaway_tests": len(xlsx_files),
                "dcp_tests": 0,
                "borehole_logs": bh_count,
            })

        elif path.suffix.lower() == ".xlsx":
            if "soakaway" in path.name.lower():
                soakaway_reports.append(parse_soakaway_xlsx(path))

            import_summary.append({
                "file": file.name,
                "type": kind,
                "locations": "",
                "groups": "XLSX",
                "soakaway_tests": 1,
                "dcp_tests": 0,
            })

    st.session_state.loaded_files = loaded_files
    st.session_state.parsed_zips = parsed_zips
    st.session_state.soakaway_reports = soakaway_reports
    st.session_state.dcp_tests = dcp_tests
    st.session_state.import_summary = import_summary

    if not st.session_state.borehole_strip_layout:
        st.session_state.borehole_strip_layout = default_strip_layout()

    for test in dcp_tests:
        project_id = str(test.get("project_id") or "unknown_project")
        location_id = str(test.get("location_id") or "unknown_location")
        key = f"{project_id}::{location_id}"
        st.session_state.dcp_layer_store[key] = default_layers_for_dcp(test)


def soakaway_preview_rows():
    rows = []
    for r in st.session_state.soakaway_reports:
        rows.append({
            "project_id": r.project.get("project_id", ""),
            "project": r.project.get("project_name", ""),
            "location_id": r.test.get("location_id", ""),
            "run": r.test.get("test_run", ""),
            "date": r.test.get("test_date", ""),
            "tested_by": r.test.get("tested_by", ""),
            "readings": len(r.readings),
            "pit_depth": r.pit.get("depth_m", ""),
        })
    return rows


def dcp_preview_rows():
    rows = []
    for idx, t in enumerate(st.session_state.dcp_tests):
        rows.append({
            "index": idx,
            "project_id": t.get("project_id", ""),
            "location_id": t.get("location_id", ""),
            "DCPT rows": t.get("row_count", 0),
            "ICBR placeholder rows": len(t.get("icbr_rows", [])),
        })
    return rows


def show_downloads(downloads_key: str, label_prefix: str, mime: str = "application/pdf"):
    downloads = st.session_state.get(downloads_key, {})

    if not downloads:
        return

    st.subheader("Downloads")

    for project_id, path_str in sorted(downloads.items()):
        p = Path(path_str)

        if not p.exists():
            st.warning(f"Missing output for project {project_id}: {p}")
            continue

        data = p.read_bytes()
        st.download_button(
            label=f"{label_prefix} {project_id}",
            data=data,
            file_name=p.name,
            mime=mime,
            key=f"{downloads_key}_{project_id}_{p.stat().st_mtime_ns}",
        )


hero(
    "Report Studio",
    "Upload once. Detect AGS / Flowfinity / XLSX data, review engineering outputs, and export PDF + AGS packages.",
    badge="Report Studio Demo",
)

st.sidebar.markdown("## Report Studio")
st.sidebar.caption("Demo reporting workflow")

mode = st.sidebar.radio(
    "Workflow",
    [
        "Project Import",
        "Project Overview",
        "Report Builder",
        "Soakaway Reports",
        "DCP Dashboard",
        "Borehole Engine",
        "Full AGS Report",
        "Future Tests",
    ],
)


if mode == "Project Import":
    st.header("Project Import")
    st.write("Upload Flowfinity/AGS CSV ZIPs, XLSX proformas, or ZIPs of XLSX files once.")

    files = st.file_uploader(
        "Upload project files",
        type=["zip", "xlsx", "csv", "ags"],
        accept_multiple_files=True,
        key="project_import_uploader",
    )

    c1, c2 = st.columns([1, 1])

    with c1:
        if files and st.button("Load Project Data"):
            load_files_into_project_store(files)
            st.success("Project data loaded.")

    with c2:
        if st.button("Clear Project Store"):
            reset_project_store()
            st.warning("Project store cleared.")

    if st.session_state.import_summary:
        st.subheader("Import Summary")
        st.dataframe(pd.DataFrame(st.session_state.import_summary), use_container_width=True)

    if st.session_state.loaded_files:
        st.subheader("Loaded Files")
        st.dataframe(pd.DataFrame(st.session_state.loaded_files), use_container_width=True)


elif mode == "Project Overview":
    st.header("Project Overview")

    if not st.session_state.loaded_files:
        st.warning("No project data loaded yet. Go to Project Import first.")
    else:
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Files loaded", len(st.session_state.loaded_files))
        c2.metric("Soakaway tests", len(st.session_state.soakaway_reports))
        c3.metric("DCP tests", len(st.session_state.dcp_tests))
        c4.metric("Borehole logs", len(st.session_state.borehole_reports))

        st.subheader("Import Summary")
        st.dataframe(pd.DataFrame(st.session_state.import_summary), use_container_width=True)

        if st.session_state.parsed_zips:
            st.subheader("Locations from first ZIP")
            parsed = st.session_state.parsed_zips[0]
            st.dataframe(pd.DataFrame(location_summary(parsed)), use_container_width=True)


elif mode == "Report Builder":
    render_report_builder_page(OUTPUT)


elif mode == "Soakaway Reports":
    st.header("Soakaway Reports")
    st.caption("Uses the shared project import. Exports PDF and ISAG/ISAT AGS CSV ZIP.")

    rows = soakaway_preview_rows()

    if not rows:
        st.warning("No soakaway tests loaded.")
    else:
        st.subheader("Detected Soakaway Tests")
        st.dataframe(pd.DataFrame(rows), use_container_width=True)

        c1, c2 = st.columns(2)

        with c1:
            if st.button("Generate Soakaway PDFs"):
                by_project = defaultdict(list)

                for report in st.session_state.soakaway_reports:
                    project_id = str(report.project.get("project_id") or "unknown_project").strip() or "unknown_project"
                    by_project[project_id].append(report)

                downloads = {}

                for project_id, project_reports in sorted(by_project.items()):
                    project_output = OUTPUT / project_id
                    project_output.mkdir(parents=True, exist_ok=True)

                    pdfs = []
                    for report in project_reports:
                        pdfs.append(export_soakaway_pdf(report, project_output))

                    merged = project_output / f"{project_id}_soakaway_merged.pdf"
                    merge_pdfs(pdfs, merged)
                    downloads[project_id] = str(merged)

                st.session_state.soakaway_downloads = downloads
                st.success(f"Generated soakaway merged PDFs for {len(downloads)} project(s).")

        with c2:
            if st.button("Export Soakaway AGS CSV ZIP"):
                outputs = export_soakaway_ags_zip_by_project(
                    st.session_state.soakaway_reports,
                    OUTPUT,
                )
                st.session_state.soakaway_ags_downloads = {
                    project_id: str(path)
                    for project_id, path in outputs.items()
                }
                st.success(f"Generated soakaway AGS CSV ZIPs for {len(outputs)} project(s).")

            if st.button("Export Soakaway AGS File"):
                outputs = export_soakaway_ags_file_by_project(
                    st.session_state.soakaway_reports,
                    OUTPUT,
                )
                st.session_state.soakaway_ags_file_downloads = {
                    project_id: str(path)
                    for project_id, path in outputs.items()
                }
                st.success(f"Generated soakaway AGS files for {len(outputs)} project(s).")

        show_downloads("soakaway_downloads", "Download Soakaway PDF", "application/pdf")
        show_downloads("soakaway_ags_downloads", "Download Soakaway AGS ZIP", "application/zip")
        show_downloads("soakaway_ags_file_downloads", "Download Soakaway AGS File", "text/plain")


elif mode == "DCP Dashboard":
    st.header("DCP Dashboard")
    st.caption("Click DCP markers where penetration behaviour changes. Clicked depths become layer breaks and update ICBR.")

    rows = dcp_preview_rows()

    if not rows:
        st.warning("No DCP tests loaded. Go to Project Import and upload Flowfinity DCPG/DCPT ZIPs.")
    else:
        selected_label = st.selectbox(
            "Select DCP location",
            options=[
                f"{row['project_id']} / {row['location_id']} / index {row['index']}"
                for row in rows
            ],
        )

        selected_index = int(selected_label.split("index ")[-1])
        dcp_test = st.session_state.dcp_tests[selected_index]

        project_id = str(dcp_test.get("project_id") or "unknown_project")
        location_id = str(dcp_test.get("location_id") or "unknown_location")
        key = f"{project_id}::{location_id}"

        break_key = f"dcp_breaks::{key}"

        if key not in st.session_state.dcp_layer_store:
            st.session_state.dcp_layer_store[key] = default_layers_for_dcp(dcp_test)

        if break_key not in st.session_state:
            st.session_state[break_key] = []

        st.subheader("DCP Plot: Depth vs Blows")
        st.write("Click markers on the graph. Each clicked marker depth is added as a layer break.")

        fig = make_dcp_plotly_figure(dcp_test, st.session_state.dcp_layer_store[key])

        clicked_points = plotly_events(
            fig,
            click_event=True,
            select_event=False,
            hover_event=False,
            override_height=650,
            key=f"dcp_click_plot_{key}",
        )

        if clicked_points:
            for pt in clicked_points:
                depth = pt.get("y")
                if depth is None:
                    continue

                try:
                    depth = round(float(depth), 3)
                except Exception:
                    continue

                if depth > 0 and depth not in st.session_state[break_key]:
                    st.session_state[break_key].append(depth)

            st.session_state[break_key] = sorted(set(st.session_state[break_key]))

        csel1, csel2, csel3, csel4 = st.columns([1.5, 1, 1, 2])

        with csel1:
            st.write("Current clicked break depths:")
            if st.session_state[break_key]:
                st.code(", ".join(str(d) for d in st.session_state[break_key]))
            else:
                st.write("None yet.")

        with csel2:
            if st.button("Apply Clicked Breaks"):
                st.session_state.dcp_layer_store[key] = layers_from_break_depths(
                    dcp_test,
                    st.session_state[break_key],
                    method="min",
                )
                st.success("Layer breaks applied from clicked DCP points.")

        with csel3:
            if st.button("Clear Breaks"):
                st.session_state[break_key] = []
                st.session_state.dcp_layer_store[key] = default_layers_for_dcp(dcp_test)
                st.warning("Layer breaks cleared.")

        with csel4:
            manual_breaks = st.text_input(
                "Manual break depths, comma-separated",
                value="",
                placeholder="0.35, 0.75, 1.10",
                key=f"manual_breaks_{key}",
            )

            if st.button("Apply Manual Breaks"):
                depths = []

                for part in manual_breaks.split(","):
                    part = part.strip()
                    if not part:
                        continue
                    try:
                        depths.append(round(float(part), 3))
                    except Exception:
                        pass

                st.session_state[break_key] = sorted(set(depths))
                st.session_state.dcp_layer_store[key] = layers_from_break_depths(
                    dcp_test,
                    st.session_state[break_key],
                    method="min",
                )
                st.success("Layer breaks applied from manual depths.")

        st.subheader("Layer Editor")

        layer_df = pd.DataFrame(st.session_state.dcp_layer_store[key])

        edited = st.data_editor(
            layer_df,
            use_container_width=True,
            num_rows="dynamic",
            column_config={
                "from_m": st.column_config.NumberColumn("From (m)", step=0.05, format="%.3f"),
                "to_m": st.column_config.NumberColumn("To (m)", step=0.05, format="%.3f"),
                "layer": st.column_config.TextColumn("Layer"),
                "method": st.column_config.SelectboxColumn(
                    "Method",
                    options=["min", "mean", "median", "max", "manual"],
                ),
                "manual_icbr": st.column_config.TextColumn("Manual ICBR"),
            },
            key=f"layer_editor_{key}",
        )

        st.session_state.dcp_layer_store[key] = edited.to_dict(orient="records")

        calculated_layers = calculate_layer_icbr(
            dcp_test,
            st.session_state.dcp_layer_store[key],
        )

        st.subheader("Calculated ICBR Layers")
        st.dataframe(pd.DataFrame(calculated_layers), use_container_width=True)

        st.subheader("Preview ICBR AGS Rows")
        icbr_rows = icbr_rows_from_layers(
            dcp_test,
            st.session_state.dcp_layer_store[key],
        )
        st.dataframe(pd.DataFrame(icbr_rows), use_container_width=True)

        c1, c2 = st.columns(2)

        with c1:
            if st.button("Generate DCP PDFs"):
                by_project = defaultdict(list)

                for test in st.session_state.dcp_tests:
                    pid = str(test.get("project_id") or "unknown_project").strip() or "unknown_project"
                    by_project[pid].append(test)

                downloads = {}

                for pid, tests in sorted(by_project.items()):
                    project_output = OUTPUT / pid
                    project_output.mkdir(parents=True, exist_ok=True)

                    pdfs = []
                    for test in tests:
                        loc = str(test.get("location_id") or "unknown_location")
                        layer_key = f"{pid}::{loc}"
                        layers = st.session_state.dcp_layer_store.get(layer_key, [])
                        pdfs.append(export_dcp_pdf(test, project_output, layers))

                    merged = project_output / f"{pid}_dcp_merged.pdf"
                    merge_pdfs(pdfs, merged)
                    downloads[pid] = str(merged)

                st.session_state.dcp_downloads = downloads
                st.success(f"Generated DCP merged PDFs for {len(downloads)} project(s).")

        with c2:
            if st.button("Export DCP + ICBR AGS CSV ZIP"):
                outputs = export_dcp_ags_zip_by_project(
                    st.session_state.dcp_tests,
                    st.session_state.dcp_layer_store,
                    OUTPUT,
                )
                st.session_state.dcp_ags_downloads = {
                    project_id: str(path)
                    for project_id, path in outputs.items()
                }
                st.success(f"Generated DCP/ICBR AGS CSV ZIPs for {len(outputs)} project(s).")

            if st.button("Export DCP + ICBR AGS File"):
                outputs = export_dcp_ags_file_by_project(
                    st.session_state.dcp_tests,
                    st.session_state.dcp_layer_store,
                    OUTPUT,
                )
                st.session_state.dcp_ags_file_downloads = {
                    project_id: str(path)
                    for project_id, path in outputs.items()
                }
                st.success(f"Generated DCP/ICBR AGS files for {len(outputs)} project(s).")

        show_downloads("dcp_downloads", "Download DCP PDF", "application/pdf")
        show_downloads("dcp_ags_downloads", "Download DCP/ICBR AGS ZIP", "application/zip")
        show_downloads("dcp_ags_file_downloads", "Download DCP/ICBR AGS File", "text/plain")

elif mode == "Borehole Logs":
    st.header("Borehole Logs")
    st.caption("Reads AGS files and creates borehole log PDFs from LOCA / GEOL / SAMP.")

    reports = st.session_state.borehole_reports

    if not reports:
        st.warning("No borehole logs loaded. Go to Project Import and upload an .ags file containing LOCA and GEOL.")
    else:
        rows = []
        for idx, r in enumerate(reports):
            rows.append({
                "index": idx,
                "project_id": r.project.project_id,
                "location_id": r.test.location_id,
                "type": r.borehole.type,
                "final_depth": r.borehole.final_depth,
                "strata_rows": len(r.borehole.strata),
                "sample_rows": len(r.borehole.samples),
            })

        st.subheader("Detected Borehole Logs")
        st.dataframe(pd.DataFrame(rows), use_container_width=True)

        selected = st.selectbox(
            "Preview borehole",
            options=[f"{row['project_id']} / {row['location_id']} / index {row['index']}" for row in rows],
        )

        selected_index = int(selected.split("index ")[-1])
        report = reports[selected_index]

        c1, c2 = st.columns(2)

        with c1:
            st.subheader("Strata")
            st.dataframe(pd.DataFrame(report.borehole.strata), use_container_width=True)

        with c2:
            st.subheader("Samples")
            st.dataframe(pd.DataFrame(report.borehole.samples), use_container_width=True)

        if st.button("Generate Borehole Log PDFs"):
            by_project = defaultdict(list)

            for r in reports:
                pid = str(r.project.project_id or "unknown_project").strip() or "unknown_project"
                by_project[pid].append(r)

            downloads = {}

            for pid, project_reports in sorted(by_project.items()):
                project_output = OUTPUT / pid
                project_output.mkdir(parents=True, exist_ok=True)

                pdfs = []
                for r in project_reports:
                    pdfs.append(export_borehole_pdf(r, project_output))

                merged = project_output / f"{pid}_borehole_logs_merged.pdf"
                merge_pdfs(pdfs, merged)
                downloads[pid] = str(merged)

            st.session_state.borehole_downloads = downloads
            st.success(f"Generated borehole log PDFs for {len(downloads)} project(s).")

        show_downloads("borehole_downloads", "Download Borehole Logs PDF", "application/pdf")


elif mode == "Borehole Engine":
    st.header("Borehole Engine")
    st.caption("1:50 depth-scaled strip engine. Configure strips, lanes, order and widths. Optional DCP / ICBR / soakaway depth strips can be enabled.")

    if not st.session_state.borehole_strip_layout:
        st.session_state.borehole_strip_layout = default_strip_layout()

    reports = st.session_state.borehole_reports

    with st.expander("Available strip registry"):
        registry_df = pd.DataFrame(registry_rows())
        st.dataframe(registry_df, use_container_width=True)

    st.subheader("Strip Layout Editor")
    st.write("Depth scale and level scale are fixed edge strips. Configure the middle strips below.")

    layout_df = pd.DataFrame(st.session_state.borehole_strip_layout)

    category_options = ["All"] + categories()
    selected_category = st.selectbox(
        "Filter strip editor by category",
        category_options,
        key="borehole_strip_category_filter",
    )

    if selected_category != "All":
        editor_df = layout_df[layout_df["category"] == selected_category].copy()
    else:
        editor_df = layout_df.copy()

    col_a, col_b, col_c, col_d = st.columns(4)

    with col_a:
        if st.button("Enable Geotechnical"):
            for row in st.session_state.borehole_strip_layout:
                if row.get("category") == "Geotechnical":
                    row["visible"] = True
            st.success("Geotechnical strips enabled.")

    with col_b:
        if st.button("Enable Rock"):
            for row in st.session_state.borehole_strip_layout:
                if row.get("category") == "Rock":
                    row["visible"] = True
            st.success("Rock strips enabled.")

    with col_c:
        if st.button("Enable Chemistry"):
            for row in st.session_state.borehole_strip_layout:
                if row.get("category") == "Environmental / chemistry":
                    row["visible"] = True
            st.success("Chemistry strips enabled.")

    with col_d:
        if st.button("Reset Strip Layout"):
            st.session_state.borehole_strip_layout = default_strip_layout()
            st.success("Strip layout reset.")

    edited_layout = st.data_editor(
        editor_df,
        use_container_width=True,
        num_rows="fixed",
        column_config={
            "order": st.column_config.NumberColumn("Order", step=1),
            "category": st.column_config.TextColumn("Category", disabled=True),
            "key": st.column_config.TextColumn("Key", disabled=True),
            "label": st.column_config.TextColumn("Label", disabled=True),
            "visible": st.column_config.CheckboxColumn("Visible"),
            "width_mm": st.column_config.NumberColumn("Requested Width (mm)", step=1, format="%.1f"),
        },
        key=f"borehole_strip_layout_editor_{selected_category}",
    )

    # merge filtered editor result back into full layout
    edited_rows = edited_layout.to_dict(orient="records")
    edited_by_key = {row["key"]: row for row in edited_rows}

    merged_layout = []
    for row in st.session_state.borehole_strip_layout:
        key = row.get("key")
        if key in edited_by_key:
            merged_layout.append(edited_by_key[key])
        else:
            merged_layout.append(row)

    st.session_state.borehole_strip_layout = merged_layout

    with st.expander("Current strip layout by category"):
        grouped = pd.DataFrame(st.session_state.borehole_strip_layout)
        if not grouped.empty:
            grouped = grouped.sort_values(["category", "order"])
            st.dataframe(grouped, use_container_width=True)

    if not reports:
        st.warning("No borehole logs loaded. Go to Project Import and upload an .ags file containing LOCA and GEOL.")
    else:
        rows = []

        for idx, r in enumerate(reports):
            rows.append({
                "index": idx,
                "project_id": r.project.project_id,
                "location_id": r.test.location_id,
                "type": r.borehole.type,
                "final_depth": r.borehole.final_depth,
                "strata_rows": len(r.borehole.strata),
                "sample_rows": len(r.borehole.samples),
                "test_rows": len(r.borehole.tests),
                "water_rows": len(r.borehole.groundwater),
            })

        st.subheader("Detected Borehole Logs")
        st.dataframe(pd.DataFrame(rows), use_container_width=True)

        selected = st.selectbox(
            "Preview borehole",
            options=[f"{row['project_id']} / {row['location_id']} / index {row['index']}" for row in rows],
        )

        selected_index = int(selected.split("index ")[-1])
        report = reports[selected_index]

        c1, c2 = st.columns(2)

        with c1:
            st.subheader("Strata")
            st.dataframe(pd.DataFrame(report.borehole.strata), use_container_width=True)

            st.subheader("Samples")
            st.dataframe(pd.DataFrame(report.borehole.samples), use_container_width=True)

        with c2:
            st.subheader("Tests")
            st.dataframe(pd.DataFrame(report.borehole.tests), use_container_width=True)

            st.subheader("Groundwater")
            st.dataframe(pd.DataFrame(report.borehole.groundwater), use_container_width=True)

        if st.button("Generate Borehole Engine PDFs"):
            by_project = defaultdict(list)

            for r in reports:
                pid = str(r.project.project_id or "unknown_project").strip() or "unknown_project"
                by_project[pid].append(r)

            downloads = {}

            for pid, project_reports in sorted(by_project.items()):
                project_output = OUTPUT / pid
                project_output.mkdir(parents=True, exist_ok=True)

                pdfs = []

                for r in project_reports:
                    pdfs.append(
                        export_borehole_pdf(
                            report=r,
                            output_dir=project_output,
                            strip_layout_rows=st.session_state.borehole_strip_layout,
                            dcp_tests=st.session_state.dcp_tests,
                            soakaway_reports=st.session_state.soakaway_reports,
                        )
                    )

                merged = project_output / f"{pid}_borehole_engine_merged.pdf"
                merge_pdfs(pdfs, merged)
                downloads[pid] = str(merged)

            st.session_state.borehole_downloads = downloads
            st.success(f"Generated borehole engine PDFs for {len(downloads)} project(s).")

        show_downloads("borehole_downloads", "Download Borehole Engine PDF", "application/pdf")


elif mode == "Full AGS Report":
    st.header("Full AGS Report")
    st.caption("Creates a complete PDF report from all AGS data: group inventory, locations, coverage matrix, depth plots, and group previews.")

    parsed_files = st.session_state.get("ags_files", [])

    if not parsed_files:
        st.warning("No AGS files loaded. Go to Project Import and upload a .ags file first.")
    else:
        st.subheader("Loaded AGS Files")

        rows = []
        for idx, parsed in enumerate(parsed_files):
            group_count = len(parsed.get("groups", {}))
            row_count = sum(len(v) for v in parsed.get("groups", {}).values())
            loca_count = len(parsed.get("groups", {}).get("LOCA", []))

            rows.append({
                "index": idx,
                "file": parsed.get("name", ""),
                "groups": group_count,
                "rows": row_count,
                "locations": loca_count,
            })

        st.dataframe(pd.DataFrame(rows), use_container_width=True)

        st.write("This report includes every AGS group, but it also creates depth plots for known depth-related groups like GEOL, SAMP, ISPT, WSTD, CORE, DCPT, ICBR, ISAT, IVAN and IPID.")

        if st.button("Generate Full AGS Report PDF"):
            output_path = export_full_ags_report(parsed_files, OUTPUT)
            st.session_state.full_report_downloads = {
                "Full AGS Report": str(output_path)
            }
            st.success("Generated Full AGS Report PDF.")

        show_downloads("full_report_downloads", "Download Full AGS Report", "application/pdf")


else:
    st.header("Future Tests")
    st.write("These will use the same Project Import store:")
    st.write("- Hand Vane / IVAN")
    st.write("- PID / IPID")
    st.write("- Plate Load")
    st.write("- Lab CBR")
