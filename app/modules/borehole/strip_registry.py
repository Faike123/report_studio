from __future__ import annotations


AVAILABLE_STRIPS = {
    # -------------------------
    # Core / operational
    # -------------------------
    "progress": {
        "category": "Core log",
        "label": "Progress",
        "default_width_mm": 12,
        "default_visible": True,
        "kind": "interval",
        "lanes": [
            {"key": "progress", "label": "Progress", "kind": "interval_text"},
        ],
    },

    # -------------------------
    # Geology
    # -------------------------
    "legend": {
        "category": "Geology",
        "label": "Legend",
        "default_width_mm": 18,
        "default_visible": True,
        "kind": "interval_symbol",
        "lanes": [
            {"key": "legend", "label": "Legend", "kind": "interval_symbol"},
        ],
    },
    "description": {
        "category": "Geology",
        "label": "Description",
        "default_width_mm": 78,
        "default_visible": True,
        "kind": "interval_text",
        "minimum_width_mm": 60,
        "lanes": [
            {"key": "description", "label": "Description", "kind": "interval_text"},
        ],
    },

    # -------------------------
    # Geotechnical
    # -------------------------
    "samples_tests": {
        "category": "Geotechnical",
        "label": "Samples / Tests",
        "default_width_mm": 24,
        "default_visible": True,
        "kind": "multi_lane",
        "lanes": [
            {"key": "samples", "label": "SAMP", "kind": "interval_symbol", "width_ratio": 0.45},
            {"key": "spt", "label": "SPT", "kind": "point_value", "width_ratio": 0.35},
            {"key": "other_tests", "label": "OTH", "kind": "point_value", "width_ratio": 0.20},
        ],
    },
    "dcp_profile": {
        "category": "Geotechnical",
        "label": "DCP",
        "default_width_mm": 16,
        "default_visible": False,
        "kind": "profile",
        "lanes": [
            {"key": "dcp", "label": "DCP", "kind": "profile"},
        ],
    },
    "icbr_profile": {
        "category": "Geotechnical",
        "label": "ICBR",
        "default_width_mm": 16,
        "default_visible": False,
        "kind": "profile",
        "lanes": [
            {"key": "icbr", "label": "ICBR", "kind": "profile"},
        ],
    },
    "vane_pid_tests": {
        "category": "Geotechnical",
        "label": "Vane / PID",
        "default_width_mm": 18,
        "default_visible": False,
        "kind": "multi_lane",
        "lanes": [
            {"key": "vane", "label": "HV", "kind": "point_value", "width_ratio": 0.50},
            {"key": "pid", "label": "PID", "kind": "point_value", "width_ratio": 0.50},
        ],
    },

    # -------------------------
    # Hydro / installation
    # -------------------------
    "water_installation": {
        "category": "Hydro / installation",
        "label": "Water / Installation",
        "default_width_mm": 18,
        "default_visible": True,
        "kind": "multi_lane",
        "lanes": [
            {"key": "water", "label": "W", "kind": "point_symbol", "width_ratio": 0.34},
            {"key": "standing", "label": "SWL", "kind": "point_symbol", "width_ratio": 0.33},
            {"key": "pipe", "label": "Pipe", "kind": "interval_symbol", "width_ratio": 0.33},
        ],
    },
    "casing_backfill": {
        "category": "Hydro / installation",
        "label": "Casing / Backfill",
        "default_width_mm": 16,
        "default_visible": True,
        "kind": "multi_lane",
        "lanes": [
            {"key": "casing", "label": "Cas.", "kind": "interval_symbol", "width_ratio": 0.5},
            {"key": "backfill", "label": "Back.", "kind": "interval_symbol", "width_ratio": 0.5},
        ],
    },
    "soakaway_depth": {
        "category": "Hydro / installation",
        "label": "Soakaway",
        "default_width_mm": 16,
        "default_visible": False,
        "kind": "profile",
        "lanes": [
            {"key": "soakaway", "label": "SA", "kind": "profile"},
        ],
    },

    # -------------------------
    # Rock
    # -------------------------
    "rock_quality": {
        "category": "Rock",
        "label": "Rock Quality",
        "default_width_mm": 28,
        "default_visible": False,
        "kind": "multi_lane_numeric",
        "lanes": [
            {"key": "tcr", "label": "TCR", "kind": "interval_numeric", "width_ratio": 0.33},
            {"key": "scr", "label": "SCR", "kind": "interval_numeric", "width_ratio": 0.33},
            {"key": "rqd", "label": "RQD", "kind": "interval_numeric", "width_ratio": 0.34},
        ],
    },
    "fractures": {
        "category": "Rock",
        "label": "Fractures",
        "default_width_mm": 14,
        "default_visible": False,
        "kind": "point_symbol",
        "lanes": [
            {"key": "fractures", "label": "Frac.", "kind": "point_symbol"},
        ],
    },

    # -------------------------
    # Environmental / chemistry
    # -------------------------
    "chem_results": {
        "category": "Environmental / chemistry",
        "label": "Chemistry",
        "default_width_mm": 22,
        "default_visible": False,
        "kind": "multi_lane_numeric",
        "lanes": [
            {"key": "ph", "label": "pH", "kind": "point_value", "width_ratio": 0.33},
            {"key": "sulphate", "label": "SO4", "kind": "point_value", "width_ratio": 0.34},
            {"key": "contam", "label": "Cont.", "kind": "point_value", "width_ratio": 0.33},
        ],
    },
    "lab_results": {
        "category": "Environmental / chemistry",
        "label": "Lab Results",
        "default_width_mm": 22,
        "default_visible": False,
        "kind": "multi_lane_numeric",
        "lanes": [
            {"key": "moisture", "label": "MC", "kind": "point_value", "width_ratio": 0.33},
            {"key": "plasticity", "label": "PI", "kind": "point_value", "width_ratio": 0.33},
            {"key": "other_lab", "label": "Lab", "kind": "point_value", "width_ratio": 0.34},
        ],
    },
    "eres_profile": {
        "category": "Environmental / chemistry",
        "label": "ERES",
        "default_width_mm": 16,
        "default_visible": False,
        "kind": "profile",
        "lanes": [
            {"key": "eres", "label": "ERES", "kind": "profile"},
        ],
    },

    # -------------------------
    # Custom / advanced
    # -------------------------
    "custom_depth_strip": {
        "category": "Custom / advanced",
        "label": "Custom",
        "default_width_mm": 16,
        "default_visible": False,
        "kind": "custom",
        "lanes": [
            {"key": "custom", "label": "Custom", "kind": "custom"},
        ],
    },
}


DEFAULT_ORDER = [
    "progress",
    "samples_tests",
    "water_installation",
    "casing_backfill",
    "legend",
    "description",
]


CATEGORY_ORDER = [
    "Core log",
    "Geology",
    "Geotechnical",
    "Hydro / installation",
    "Rock",
    "Environmental / chemistry",
    "Custom / advanced",
]


def default_strip_layout() -> list[dict]:
    layout = []

    for index, key in enumerate(DEFAULT_ORDER, start=1):
        spec = AVAILABLE_STRIPS[key]
        layout.append({
            "order": index,
            "category": spec["category"],
            "key": key,
            "label": spec["label"],
            "visible": spec["default_visible"],
            "width_mm": spec["default_width_mm"],
        })

    optional_index = len(layout) + 1

    for category in CATEGORY_ORDER:
        for key, spec in AVAILABLE_STRIPS.items():
            if key in DEFAULT_ORDER:
                continue
            if spec["category"] != category:
                continue

            layout.append({
                "order": optional_index,
                "category": spec["category"],
                "key": key,
                "label": spec["label"],
                "visible": spec["default_visible"],
                "width_mm": spec["default_width_mm"],
            })
            optional_index += 1

    return layout


def registry_rows() -> list[dict]:
    rows = []

    for category in CATEGORY_ORDER:
        for key, spec in AVAILABLE_STRIPS.items():
            if spec["category"] != category:
                continue

            rows.append({
                "category": spec["category"],
                "key": key,
                "label": spec["label"],
                "kind": spec["kind"],
                "default_width_mm": spec["default_width_mm"],
                "default_visible": spec["default_visible"],
                "lanes": ", ".join(lane["label"] for lane in spec.get("lanes", [])),
            })

    return rows


def categories() -> list[str]:
    return CATEGORY_ORDER[:]
