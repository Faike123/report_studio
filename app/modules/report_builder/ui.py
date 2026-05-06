from __future__ import annotations

from pathlib import Path
import pandas as pd
import streamlit as st
from app.ui.igne_theme import hero, stepbar

from app.modules.report_builder.detector import (
    detect_report_items,
    queue_summary,
    queue_table,
    selected_review_indices,
    next_unconfirmed_index,
)
from app.modules.report_builder.exporters import export_confirmed_items

from app.modules.dcp.layers import (
    default_layers_for_dcp,
    layers_from_break_depths,
    calculate_layer_icbr,
    icbr_rows_from_layers,
)
from app.modules.dcp.dashboard import make_dcp_plotly_figure

try:
    from streamlit_plotly_events import plotly_events
except Exception:
    plotly_events = None


def _get(obj, key, default=""):
    if obj is None:
        return default

    if isinstance(obj, dict):
        return obj.get(key, default)

    return getattr(obj, key, default)


def _ensure_builder_state():
    if "report_builder_items" not in st.session_state:
        st.session_state.report_builder_items = []

    if "report_builder_current_index" not in st.session_state:
        st.session_state.report_builder_current_index = 0

    if "report_builder_outputs" not in st.session_state:
        st.session_state.report_builder_outputs = {}

    if "report_builder_stage" not in st.session_state:
        st.session_state.report_builder_stage = "detect"


def _build_queue_from_session():
    st.session_state.report_builder_items = detect_report_items(
        borehole_reports=st.session_state.get("borehole_reports", []),
        soakaway_reports=st.session_state.get("soakaway_reports", []),
        dcp_tests=st.session_state.get("dcp_tests", []),
        ags_files=st.session_state.get("ags_files", []),
    )

    idx = next_unconfirmed_index(st.session_state.report_builder_items)
    st.session_state.report_builder_current_index = idx if idx is not None else 0
    st.session_state.report_builder_stage = "select"


def _update_items_from_editor(editor_df: pd.DataFrame):
    edited = editor_df.to_dict(orient="records")
    by_index = {int(row["queue_index"]): row for row in edited}

    new_items = []

    for idx, item in enumerate(st.session_state.report_builder_items):
        if idx in by_index:
            row = by_index[idx]
            new_item = dict(item)
            new_item["selected"] = bool(row.get("selected", False))

            if not new_item["selected"] and new_item.get("status") not in ("exported", "error"):
                new_item["status"] = "excluded"

            if new_item["selected"] and new_item.get("status") == "excluded":
                new_item["status"] = "needs_review" if new_item.get("requires_review") else "detected"

            new_items.append(new_item)
        else:
            new_items.append(item)

    st.session_state.report_builder_items = new_items


def _set_item_status(index: int, status: str):
    items = st.session_state.report_builder_items
    if 0 <= index < len(items):
        items[index]["status"] = status
        st.session_state.report_builder_items = items


def _go_next():
    indices = selected_review_indices(st.session_state.report_builder_items)

    if not indices:
        st.session_state.report_builder_current_index = 0
        return

    current = st.session_state.report_builder_current_index

    if current not in indices:
        st.session_state.report_builder_current_index = indices[0]
        return

    pos = indices.index(current)
    next_pos = min(pos + 1, len(indices) - 1)
    st.session_state.report_builder_current_index = indices[next_pos]


def _go_previous():
    indices = selected_review_indices(st.session_state.report_builder_items)

    if not indices:
        st.session_state.report_builder_current_index = 0
        return

    current = st.session_state.report_builder_current_index

    if current not in indices:
        st.session_state.report_builder_current_index = indices[0]
        return

    pos = indices.index(current)
    prev_pos = max(pos - 1, 0)
    st.session_state.report_builder_current_index = indices[prev_pos]


def _download_file(path_str: str, label: str, mime: str):
    path = Path(path_str)

    if not path.exists():
        st.warning(f"Missing output: {path}")
        return

    st.download_button(
        label=label,
        data=path.read_bytes(),
        file_name=path.name,
        mime=mime,
        key=f"download_{label}_{path.name}_{path.stat().st_mtime_ns}",
    )


def render_report_builder_page(output_root: Path):
    _ensure_builder_state()

    hero(
        "Report Builder Wizard",
        "Detect every reportable item in the loaded project data, select what to include, confirm each item, then export a complete PDF and AGS package.",
        badge="Production Workflow",
    )

    stage = "detect"
    if st.session_state.get("report_builder_items"):
        stage = "review"
    if st.session_state.get("report_builder_outputs"):
        stage = "export"

    stepbar(stage)

    c1, c2, c3 = st.columns([1, 1, 2])

    with c1:
        if st.button("Detect / Rebuild Report Queue", type="primary"):
            _build_queue_from_session()
            st.success("Report queue rebuilt from loaded project data.")

    with c2:
        if st.button("Clear Builder State"):
            st.session_state.report_builder_items = []
            st.session_state.report_builder_outputs = {}
            st.session_state.report_builder_current_index = 0
            st.session_state.report_builder_stage = "detect"
            st.warning("Report Builder state cleared.")

    with c3:
        st.write("Use this after Project Import. Manual tabs remain available for expert edits.")

    items = st.session_state.report_builder_items

    if not items:
        st.info("No report queue yet. Go to Project Import, load data, then press **Detect / Rebuild Report Queue**.")
        return

    summary = queue_summary(items)

    st.markdown("### Package Status")

    selected_count = summary["selected"]
    confirmed_count = summary["confirmed"]
    exported_count = summary["exported"]

    ready_ratio = 0
    if selected_count:
        ready_ratio = confirmed_count / selected_count

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Detected", summary["total"])
    m2.metric("Selected for report", selected_count)
    m3.metric("Confirmed", confirmed_count)
    m4.metric("Exported", exported_count)

    st.progress(ready_ratio, text=f"{confirmed_count} of {selected_count} selected items confirmed")

    if selected_count == 0:
        st.warning("No items selected for reporting yet.")
    elif confirmed_count == selected_count:
        st.success("All selected review items are confirmed and ready to export.")
    else:
        st.info("Continue reviewing selected PDF report items. Export-only AGS groups are tracked separately and do not need manual review.")

    with st.expander("Detected data categories"):
        cat_rows = [
            {"category": k, "count": v}
            for k, v in sorted(summary.get("by_category", {}).items())
        ]
        if cat_rows:
            st.dataframe(pd.DataFrame(cat_rows), use_container_width=True)

    st.subheader("Select Report Package")

    table_rows = queue_table(items)
    table_df = pd.DataFrame(table_rows)

    project_filter_options = ["All"] + sorted(table_df["project_id"].dropna().unique().tolist())
    type_filter_options = ["All"] + sorted(table_df["item_type"].dropna().unique().tolist())
    category_filter_options = ["All"] + sorted(table_df["data_category"].dropna().unique().tolist())

    fc1, fc2, fc3, fc4, fc5 = st.columns(5)

    with fc1:
        project_filter = st.selectbox("Project filter", project_filter_options, key="rb_project_filter")

    with fc2:
        category_filter = st.selectbox("Data category", category_filter_options, key="rb_category_filter")

    with fc3:
        type_filter = st.selectbox("Item type filter", type_filter_options, key="rb_type_filter")

    with fc4:
        if st.button("Select all visible"):
            visible_indices = table_df.index.tolist()
            if project_filter != "All":
                visible_indices = table_df[table_df["project_id"] == project_filter].index.tolist()
            if category_filter != "All":
                temp = table_df.loc[visible_indices]
                visible_indices = temp[temp["data_category"] == category_filter].index.tolist()
            if type_filter != "All":
                temp = table_df.loc[visible_indices]
                visible_indices = temp[temp["item_type"] == type_filter].index.tolist()

            for idx in visible_indices:
                st.session_state.report_builder_items[int(table_df.loc[idx, "queue_index"])]["selected"] = True

            st.success("Visible items selected.")

    with fc5:
        if st.button("Exclude all visible"):
            visible_indices = table_df.index.tolist()
            if project_filter != "All":
                visible_indices = table_df[table_df["project_id"] == project_filter].index.tolist()
            if category_filter != "All":
                temp = table_df.loc[visible_indices]
                visible_indices = temp[temp["data_category"] == category_filter].index.tolist()
            if type_filter != "All":
                temp = table_df.loc[visible_indices]
                visible_indices = temp[temp["item_type"] == type_filter].index.tolist()

            for idx in visible_indices:
                qidx = int(table_df.loc[idx, "queue_index"])
                st.session_state.report_builder_items[qidx]["selected"] = False
                if st.session_state.report_builder_items[qidx]["status"] not in ("exported", "error"):
                    st.session_state.report_builder_items[qidx]["status"] = "excluded"

            st.warning("Visible items excluded.")

    filtered_df = table_df.copy()

    if project_filter != "All":
        filtered_df = filtered_df[filtered_df["project_id"] == project_filter]

    if category_filter != "All":
        filtered_df = filtered_df[filtered_df["data_category"] == category_filter]

    if type_filter != "All":
        filtered_df = filtered_df[filtered_df["item_type"] == type_filter]

    edited = st.data_editor(
        filtered_df,
        use_container_width=True,
        hide_index=True,
        num_rows="fixed",
        column_config={
            "queue_index": st.column_config.NumberColumn("Queue", disabled=True),
            "selected": st.column_config.CheckboxColumn("Report?"),
            "status": st.column_config.TextColumn("Status", disabled=True),
            "data_category": st.column_config.TextColumn("Category", disabled=True),
            "project_id": st.column_config.TextColumn("Project", disabled=True),
            "location_id": st.column_config.TextColumn("Location", disabled=True),
            "item_type": st.column_config.TextColumn("Type", disabled=True),
            "label": st.column_config.TextColumn("Item", disabled=True),
            "summary": st.column_config.TextColumn("Summary", disabled=True),
            "dependency": st.column_config.TextColumn("Dependency", disabled=True),
        },
        key=f"report_builder_selection_editor_{project_filter}_{category_filter}_{type_filter}",
    )

    _update_items_from_editor(edited)

    st.subheader("Guided Review Queue")

    review_indices = selected_review_indices(st.session_state.report_builder_items)

    if not review_indices:
        st.info("No selected review items. Select at least one report item above.")
    else:
        current_index = st.session_state.report_builder_current_index

        if current_index not in review_indices:
            current_index = review_indices[0]
            st.session_state.report_builder_current_index = current_index

        item = st.session_state.report_builder_items[current_index]

        pos = review_indices.index(current_index) + 1
        total = len(review_indices)

        st.markdown("---")
        st.markdown(
            f"## Review {pos} of {total}"
        )

        card_col_1, card_col_2, card_col_3, card_col_4 = st.columns([1.2, 1.2, 1.4, 2.2])

        with card_col_1:
            st.metric("Project", item["project_id"])

        with card_col_2:
            st.metric("Location", item["location_id"])

        with card_col_3:
            st.metric("Type", item["item_type"].replace("_", " ").title())

        with card_col_4:
            st.write(f"**Item:** {item.get('label')}")
            st.write(f"**Status:** `{item.get('status')}`")
            st.caption(item.get("summary", ""))

        if item.get("dependency"):
            st.warning(item["dependency"])

        if item["item_type"] == "borehole_log":
            _render_borehole_review(item, current_index)

        elif item["item_type"] == "soakaway_report":
            _render_soakaway_review(item, current_index)

        elif item["item_type"] == "dcp_report":
            _render_dcp_review(item, current_index)

        nc1, nc2, nc3, nc4 = st.columns(4)

        with nc1:
            if st.button("Previous Item"):
                _go_previous()
                st.rerun()

        with nc2:
            if st.button("Confirm + Next", type="primary"):
                _set_item_status(current_index, "confirmed")
                _go_next()
                st.success("Item confirmed.")
                st.rerun()

        with nc3:
            if st.button("Exclude + Next"):
                st.session_state.report_builder_items[current_index]["selected"] = False
                _set_item_status(current_index, "excluded")
                _go_next()
                st.warning("Item excluded.")
                st.rerun()

        with nc4:
            if st.button("Next Item"):
                _go_next()
                st.rerun()

    st.subheader("Export Package")

    confirmed = [
        item for item in st.session_state.report_builder_items
        if item.get("selected") and item.get("status") in ("confirmed", "exported")
    ]

    not_ready = [
        item for item in st.session_state.report_builder_items
        if item.get("selected")
        and item.get("requires_review")
        and item.get("status") not in ("confirmed", "exported")
    ]

    ec1, ec2, ec3 = st.columns(3)
    ec1.metric("Confirmed/exportable", len(confirmed))
    ec2.metric("Selected but not ready", len(not_ready))
    ec3.metric("Projects", len(set(i["project_id"] for i in confirmed)))

    if not_ready:
        with st.expander("Selected items not ready"):
            st.dataframe(pd.DataFrame(not_ready), use_container_width=True)

    export_disabled = len(confirmed) == 0

    if export_disabled:
        st.warning("Confirm at least one selected item before exporting.")

    if st.button("Export All Confirmed Items", type="primary", disabled=export_disabled):
        result = export_confirmed_items(
            items=st.session_state.report_builder_items,
            output_root=output_root,
            borehole_reports=st.session_state.get("borehole_reports", []),
            soakaway_reports=st.session_state.get("soakaway_reports", []),
            dcp_tests=st.session_state.get("dcp_tests", []),
            ags_files=st.session_state.get("ags_files", []),
            strip_layout_rows=st.session_state.get("borehole_strip_layout", []),
            dcp_layer_store=st.session_state.get("dcp_layer_store", {}),
        )

        st.session_state.report_builder_items = result["items"]
        st.session_state.report_builder_outputs = result

        exported_count = sum(
            1 for item in result["items"]
            if item.get("status") == "exported"
        )

        if exported_count:
            st.success(f"Export complete. Exported {exported_count} item(s).")
        else:
            st.warning("No items were exported. Confirm items first, then export.")

    outputs = st.session_state.get("report_builder_outputs", {})

    if outputs:
        st.subheader("Export Outputs")

        combined = outputs.get("combined_pdfs", {})
        ags = outputs.get("ags_outputs", {})

        if combined:
            st.write("Combined project PDFs")
            for project_id, path in combined.items():
                _download_file(path, f"Download {project_id} Combined PDF", "application/pdf")

        if ags:
            st.write("Updated AGS outputs")
            for name, path in ags.items():
                _download_file(path, f"Download {name}.ags", "text/plain")


def _render_borehole_review(item: dict, index: int):
    report = st.session_state.borehole_reports[item["source_index"]]

    st.write("Borehole log will use the global Borehole Engine strip layout.")

    c1, c2, c3 = st.columns(3)
    c1.metric("Location", _get(report.test, "location_id"))
    c2.metric("Final depth", _get(report.borehole, "final_depth"))
    c3.metric("Type", _get(report.borehole, "type"))

    tabs = st.tabs(["Strata", "Samples", "Tests", "Water", "Strip Layout"])

    with tabs[0]:
        st.dataframe(pd.DataFrame(_get(report.borehole, "strata", [])), use_container_width=True)

    with tabs[1]:
        st.dataframe(pd.DataFrame(_get(report.borehole, "samples", [])), use_container_width=True)

    with tabs[2]:
        st.dataframe(pd.DataFrame(_get(report.borehole, "tests", [])), use_container_width=True)

    with tabs[3]:
        st.dataframe(pd.DataFrame(_get(report.borehole, "groundwater", [])), use_container_width=True)

    with tabs[4]:
        layout = st.session_state.get("borehole_strip_layout", [])
        st.dataframe(pd.DataFrame(layout), use_container_width=True)
        st.info("Edit the full strip layout in the Borehole Engine tab if you need detailed strip control.")


def _render_soakaway_review(item: dict, index: int):
    report = st.session_state.soakaway_reports[item["source_index"]]

    c1, c2, c3, c4 = st.columns(4)

    c1.metric("Location", report.test.get("location_id", ""))
    c2.metric("Run", report.test.get("test_run", ""))
    c3.metric("Readings", len(report.readings))
    c4.metric("f", report.calculations.get("infiltration_rate", ""))

    st.write("Pit dimensions")
    st.dataframe(pd.DataFrame([report.pit]), use_container_width=True)

    st.write("Readings")
    st.dataframe(pd.DataFrame(report.readings), use_container_width=True)

    st.write("Calculated parameters")
    st.dataframe(pd.DataFrame([report.calculations]), use_container_width=True)


def _render_dcp_review(item: dict, index: int):
    test = st.session_state.dcp_tests[item["source_index"]]

    project_id = str(test.get("project_id") or "unknown_project")
    location_id = str(test.get("location_id") or "unknown_location")
    key = f"{project_id}::{location_id}"
    break_key = f"rb_dcp_breaks::{key}"

    if "dcp_layer_store" not in st.session_state:
        st.session_state.dcp_layer_store = {}

    if key not in st.session_state.dcp_layer_store:
        st.session_state.dcp_layer_store[key] = default_layers_for_dcp(test)

    if break_key not in st.session_state:
        st.session_state[break_key] = []

    c1, c2, c3 = st.columns(3)
    c1.metric("Location", location_id)
    c2.metric("DCPT rows", len(test.get("data", []) or []))
    c3.metric("Layer count", len(st.session_state.dcp_layer_store[key]))

    st.write("DCP plot: depth vs blows. Click markers or type break depths manually.")

    fig = make_dcp_plotly_figure(test, st.session_state.dcp_layer_store[key])

    if plotly_events is not None:
        clicked = plotly_events(
            fig,
            click_event=True,
            select_event=False,
            hover_event=False,
            override_height=520,
            key=f"rb_dcp_plot_{key}",
        )

        if clicked:
            for pt in clicked:
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
    else:
        st.plotly_chart(fig, use_container_width=True)

    bc1, bc2, bc3 = st.columns([1, 1, 2])

    with bc1:
        st.write("Clicked break depths")
        if st.session_state[break_key]:
            st.code(", ".join(str(d) for d in st.session_state[break_key]))
        else:
            st.write("None")

        if st.button("Apply Clicked Breaks", key=f"rb_apply_clicked_{key}"):
            st.session_state.dcp_layer_store[key] = layers_from_break_depths(
                test,
                st.session_state[break_key],
                method="min",
            )
            st.success("Clicked breaks applied.")

    with bc2:
        if st.button("Clear DCP Breaks", key=f"rb_clear_dcp_{key}"):
            st.session_state[break_key] = []
            st.session_state.dcp_layer_store[key] = default_layers_for_dcp(test)
            st.warning("DCP breaks cleared.")

    with bc3:
        manual = st.text_input(
            "Manual break depths",
            placeholder="0.35, 0.80, 1.20",
            key=f"rb_manual_breaks_{key}",
        )

        if st.button("Apply Manual Breaks", key=f"rb_apply_manual_{key}"):
            depths = []
            for part in manual.split(","):
                part = part.strip()
                if not part:
                    continue
                try:
                    depths.append(round(float(part), 3))
                except Exception:
                    pass

            st.session_state[break_key] = sorted(set(depths))
            st.session_state.dcp_layer_store[key] = layers_from_break_depths(
                test,
                depths,
                method="min",
            )
            st.success("Manual breaks applied.")

    layer_df = pd.DataFrame(st.session_state.dcp_layer_store[key])

    edited_layers = st.data_editor(
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
        key=f"rb_dcp_layers_{key}",
    )

    st.session_state.dcp_layer_store[key] = edited_layers.to_dict(orient="records")

    calculated = calculate_layer_icbr(test, st.session_state.dcp_layer_store[key])
    icbr_rows = icbr_rows_from_layers(test, st.session_state.dcp_layer_store[key])

    st.write("Calculated ICBR layers")
    st.dataframe(pd.DataFrame(calculated), use_container_width=True)

    st.write("Preview ICBR AGS rows")
    st.dataframe(pd.DataFrame(icbr_rows), use_container_width=True)
