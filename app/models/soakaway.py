from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class SoakawayReport:
    project: dict = field(default_factory=dict)
    test: dict = field(default_factory=dict)
    location: dict = field(default_factory=dict)
    pit: dict = field(default_factory=dict)
    readings: list = field(default_factory=list)
    calculations: dict = field(default_factory=dict)
    strata: list = field(default_factory=list)
    subfooter: dict = field(default_factory=dict)
    signoff: dict = field(default_factory=dict)
    page: dict = field(default_factory=dict)


def empty_soakaway_report() -> SoakawayReport:
    return SoakawayReport(
        project={
            "project_name": "",
            "client": "",
            "project_engineer": "",
            "project_id": "",
        },
        test={
            "location_id": "",
            "test_run": "1",
            "test_date": "",
            "tested_by": "",
            "weather": "",
        },
        location={
            "easting": "",
            "northing": "",
            "ground_level": "",
        },
        pit={
            "length_m": "",
            "width_m": "",
            "depth_m": "",
        },
        readings=[],
        calculations={},
        strata=[
            {"from": "0", "to": "0.5", "description": "Gravelly sandy TOPSOIL with cobbles"},
            {"from": "0.5", "to": "1.5", "description": "Slightly gravelly silty SAND with cobbles"},
        ],
        subfooter={
            "remarks": "",
            "instrument": "",
            "methodology": "BRE 365 Digest rev. 2016",
        },
        signoff={
            "originator": "TK",
            "status": "Prelim",
            "checked_approved": "",
            "issue_date": "",
        },
        page={
            "fig_no": "",
            "current": 1,
            "total": 1,
        },
    )
