#!/usr/bin/env python3
"""Hard release gates: no exclusions, DRC errors, or missing copper."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PROJECT = ROOT / "chess-board.kicad_pro"
CONNECTIVITY = ROOT / "design" / "netlist.json"
REPORT = ROOT / "generated" / "drc.json"


def validate() -> None:
    project = json.loads(PROJECT.read_text())
    exclusions = project.get("board", {}).get("design_settings", {}).get(
        "drc_exclusions", []
    )
    if exclusions:
        raise SystemExit(f"release blocked: {len(exclusions)} DRC exclusions")

    source = json.loads(CONNECTIVITY.read_text())["projects"]["board"]
    for index, connection in enumerate(source["connections"], 1):
        pads = connection["pads"]
        explicit = connection.get("no_connect", False)
        if len(pads) == 1 and not explicit:
            raise SystemExit(f"connection {index} is silently unconnected")
        if len(pads) != 1 and explicit:
            raise SystemExit(f"connection {index} incorrectly bypasses routing")

    report = json.loads(REPORT.read_text())
    violations = report.get("violations", [])
    unconnected = report.get("unconnected_items", [])
    parity = report.get("schematic_parity", [])
    if violations or unconnected or parity:
        raise SystemExit(
            "release blocked: "
            f"{len(violations)} DRC violations, "
            f"{len(unconnected)} unconnected items, "
            f"{len(parity)} parity errors"
        )
    print("PCB release gate passed: no exclusions, violations, or open connections")


if __name__ == "__main__":
    validate()
