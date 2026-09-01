#!/usr/bin/env python3
"""Generate the strict KiCad project file from its reviewed JSON template."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
TEMPLATE = ROOT / "design" / "project-template.json"
PROJECT = ROOT / "generated" / "chess-board.kicad_pro"
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
    settings["drc_exclusions"] = []
    for name in STRICT_RULES:
        settings["rule_severities"][name] = "error"
    return json.dumps(project, indent=2, sort_keys=True) + "\n"


def configure() -> None:
    PROJECT.parent.mkdir(exist_ok=True)
    PROJECT.write_text(render())


if __name__ == "__main__":
    configure()
