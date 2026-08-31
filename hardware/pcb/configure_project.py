#!/usr/bin/env python3
"""Apply strict, reviewable KiCad project policy after board generation."""

from __future__ import annotations

import json
from pathlib import Path

PROJECT = Path(__file__).resolve().parent / "chess-board.kicad_pro"
STRICT_RULES = (
    "footprint_filters_mismatch",
    "footprint_type_mismatch",
    "missing_courtyard",
    "npth_inside_courtyard",
    "pth_inside_courtyard",
)


def configure() -> None:
    project = json.loads(PROJECT.read_text())
    settings = project["board"]["design_settings"]
    settings["drc_exclusions"] = []
    for name in STRICT_RULES:
        settings["rule_severities"][name] = "error"
    PROJECT.write_text(json.dumps(project, indent=2, sort_keys=True) + "\n")


if __name__ == "__main__":
    configure()
