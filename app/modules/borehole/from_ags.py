from __future__ import annotations

from types import SimpleNamespace


def _ns(**kwargs):
    return SimpleNamespace(**kwargs)


def _first(*values):
    for value in values:
        if value not in (None, ""):
            return value
    return ""


def _f(value):
    try:
        if value in (None, ""):
            return None
        return float(value)
    except Exception:
        return None


def _fmt(value, ndp=3):
    v = _f(value)
    if v is None:
        return "" if value is None else str(value)
    text = f"{v:.{ndp}f}"
    return text.rstrip("0").rstrip(".")


def _by_loca(rows: list[dict], loca_id: str) -> list[dict]:
    return [
        row for row in rows
        if str(row.get("LOCA_ID", "")).strip() == str(loca_id).strip()
    ]


def _sort_by_depth(rows: list[dict], key: str) -> list[dict]:
    return sorted(rows, key=lambda r: _f(r.get(key)) if _f(r.get(key)) is not None else 999999)


def borehole_reports_from_ags(parsed: dict) -> list:
    groups = parsed.get("groups", {})

    loca_rows = groups.get("LOCA", [])
    geol_rows = groups.get("GEOL", [])
    samp_rows = groups.get("SAMP", [])
    ispt_rows = groups.get("ISPT", [])
    wstd_rows = groups.get("WSTD", []) or groups.get("WSTG", [])
    core_rows = groups.get("CORE", [])
    frct_rows = groups.get("FRAC", []) or groups.get("FRCT", [])

    reports = []

    for loca in loca_rows:
        loca_id = loca.get("LOCA_ID", "")
        if not loca_id:
            continue

        geol = _sort_by_depth(_by_loca(geol_rows, loca_id), "GEOL_TOP")
        samp = _sort_by_depth(_by_loca(samp_rows, loca_id), "SAMP_TOP")
        ispt = _sort_by_depth(_by_loca(ispt_rows, loca_id), "ISPT_TOP")
        wstd = _sort_by_depth(_by_loca(wstd_rows, loca_id), "WSTD_DPTH")
        core = _sort_by_depth(_by_loca(core_rows, loca_id), "CORE_TOP")
        frct = _sort_by_depth(_by_loca(frct_rows, loca_id), "FRAC_DPTH")

        project_id = _first(loca.get("PROJ_ID"), parsed.get("name", "").replace(".ags", ""))
        project_name = _first(loca.get("PROJ_NAME"), loca.get("PROJ_DESC"), "")

        depth_values = []

        for row in geol:
            for k in ("GEOL_BASE", "GEOL_TOP"):
                v = _f(row.get(k))
                if v is not None:
                    depth_values.append(v)

        for row in samp:
            for k in ("SAMP_BASE", "SAMP_TOP"):
                v = _f(row.get(k))
                if v is not None:
                    depth_values.append(v)

        for row in ispt:
            v = _f(row.get("ISPT_TOP"))
            if v is not None:
                depth_values.append(v)

        final_depth = max(depth_values) if depth_values else _f(loca.get("LOCA_FDEP")) or 0

        strata = []
        for row in geol:
            strata.append({
                "top": _fmt(row.get("GEOL_TOP")),
                "base": _fmt(row.get("GEOL_BASE")),
                "legend": _first(row.get("GEOL_GEOL"), row.get("GEOL_LEG"), ""),
                "description": _first(row.get("GEOL_DESC"), row.get("GEOL_DESD"), row.get("GEOL_REM"), ""),
            })

        samples = []
        for row in samp:
            samples.append({
                "top": _fmt(row.get("SAMP_TOP")),
                "base": _fmt(row.get("SAMP_BASE")),
                "type": _first(row.get("SAMP_TYPE"), ""),
                "reference": _first(row.get("SAMP_REF"), row.get("SAMP_ID"), ""),
            })

        tests = []
        for row in ispt:
            tests.append({
                "depth": _fmt(row.get("ISPT_TOP")),
                "type": "SPT",
                "result": _first(row.get("ISPT_NVAL"), row.get("ISPT_MAIN"), row.get("ISPT_REP"), ""),
            })

        groundwater = []
        for row in wstd:
            groundwater.append({
                "depth": _fmt(_first(row.get("WSTD_DPTH"), row.get("WSTG_DPTH"))),
                "date": _first(row.get("WSTD_DATE"), row.get("WSTG_DATE"), ""),
                "remark": _first(row.get("WSTD_REM"), row.get("WSTG_REM"), ""),
            })

        rock = []
        for row in core:
            rock.append({
                "top": _fmt(row.get("CORE_TOP")),
                "base": _fmt(row.get("CORE_BASE")),
                "tcr": _first(row.get("CORE_PREC"), row.get("CORE_TCR"), ""),
                "scr": _first(row.get("CORE_SREC"), row.get("CORE_SCR"), ""),
                "rqd": _first(row.get("CORE_RQD"), ""),
            })

        fractures = []
        for row in frct:
            fractures.append({
                "depth": _fmt(_first(row.get("FRAC_DPTH"), row.get("FRCT_DPTH"))),
                "type": _first(row.get("FRAC_TYPE"), row.get("FRCT_TYPE"), ""),
                "description": _first(row.get("FRAC_DESC"), row.get("FRCT_DESC"), ""),
            })

        report = _ns(
            project=_ns(
                project_name=project_name,
                client=_first(loca.get("CLIENT"), loca.get("CLNT_NAME"), ""),
                project_engineer=_first(loca.get("PROJECT_ENGINEER"), ""),
                project_id=project_id,
            ),
            test=_ns(
                location_id=loca_id,
                test_run="",
                test_date=_first(loca.get("LOCA_STAR"), loca.get("LOCA_ENDD"), loca.get("LOCA_DATE"), ""),
                tested_by=_first(loca.get("LOCA_ORCO"), loca.get("LOCA_CKBY"), ""),
            ),
            location=_ns(
                easting=_fmt(_first(loca.get("LOCA_NATE"), loca.get("LOCA_LOCX"), loca.get("LOCA_X"))),
                northing=_fmt(_first(loca.get("LOCA_NATN"), loca.get("LOCA_LOCY"), loca.get("LOCA_Y"))),
                ground_level=_fmt(_first(loca.get("LOCA_GL"), loca.get("LOCA_LOCZ"), loca.get("LOCA_Z"))),
            ),
            borehole=_ns(
                final_depth=_fmt(final_depth),
                type=_first(loca.get("LOCA_TYPE"), ""),
                diameter=_first(loca.get("LOCA_DIAM"), ""),
                method=_first(loca.get("LOCA_METH"), ""),
                strata=strata,
                samples=samples,
                tests=tests,
                groundwater=groundwater,
                rock=rock,
                fractures=fractures,
                progress=[],
                casing=[],
                backfill=[],
            ),
            subfooter=_ns(
                remarks=_first(loca.get("LOCA_REM"), ""),
                instrument="Borehole / exploratory hole log",
                methodology="Generated from AGS groups LOCA / GEOL / SAMP / ISPT / WSTD",
            ),
            signoff=_ns(
                originator="TK",
                status="Prelim",
                checked_approved="",
                issue_date="",
            ),
            page=_ns(
                fig_no="",
                current="1",
                total="1",
            ),
            footer_title="BOREHOLE LOG",
            canvas_template="templates/borehole/main_canvas.html",
            logo_path="",
        )

        reports.append(report)

    return reports
