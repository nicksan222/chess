#!/usr/bin/env python3
"""Generate the strict KiCad project file from its reviewed JSON template."""

from __future__ import annotations

import json
from pathlib import Path

from board import artifacts
from domain import rules

PCB_ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = PCB_ROOT / "board" / "data" / "project-template.json"
STRICT_RULES = (
    "footprint_filters_mismatch",
    "footprint_type_mismatch",
    "missing_courtyard",
    "npth_inside_courtyard",
    "pth_inside_courtyard",
)


def render() -> str:
    project = json.loads(TEMPLATE.read_text())
    settings = project["board"]["design_settings"]
    defaults = settings["defaults"]
    defaults.update(
        {
            "board_outline_line_width": rules.OUTLINE_LINE_MM,
            "courtyard_line_width": rules.COURTYARD_LINE_MM,
            "fab_line_width": rules.FAB_LINE_MM,
            "silk_line_width": rules.SILK_LINE_MM,
            "silk_text_size_h": rules.SILK_TEXT_HEIGHT_MM,
            "silk_text_size_v": rules.SILK_TEXT_HEIGHT_MM,
            "silk_text_thickness": rules.SILK_LINE_MM,
        }
    )
    defaults["zones"]["min_clearance"] = rules.POUR_CLEARANCE_MM

    constraints = settings["rules"]
    constraints.update(
        {
            "min_clearance": rules.CLEARANCE_MM,
            "min_copper_edge_clearance": rules.POUR_TO_OUTLINE_MM,
            "min_hole_clearance": rules.HOLE_CLEARANCE_MM,
            "min_hole_to_hole": rules.HOLE_TO_HOLE_MM,
            "min_silk_clearance": rules.PCBWAY_MIN_MASK_DAM_MM,
            "min_text_height": rules.PCBWAY_MIN_SILK_TEXT_HEIGHT_MM,
            "min_text_thickness": rules.PCBWAY_MIN_SILK_LINE_MM,
            "min_through_hole_diameter": rules.PCBWAY_MIN_DRILL_MM,
            "min_track_width": rules.TRACE_WIDTH_MM,
            "min_via_annular_width": rules.annular_ring(
                rules.VIA_PAD_MM, rules.VIA_DRILL_MM
            ),
            "min_via_diameter": rules.VIA_PAD_MM,
        }
    )
    settings["drc_exclusions"] = []
    for name in STRICT_RULES:
        settings["rule_severities"][name] = "error"
    return json.dumps(project, indent=2, sort_keys=True) + "\n"


def configure() -> None:
    artifacts.GENERATED_DIR.mkdir(exist_ok=True)
    artifacts.PROJECT.write_text(render())


if __name__ == "__main__":
    configure()
