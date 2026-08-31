#!/usr/bin/env python3
"""Produce a machine-readable completeness audit for the KiCad release."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
HARDWARE = ROOT.parent
sys.path.insert(0, str(HARDWARE))
sys.path.insert(0, str(ROOT))

from shared.components import COMPONENTS  # noqa: E402
from write_bom import render as render_bom  # noqa: E402


def audit() -> dict:
    design = json.loads((ROOT / "design/netlist.json").read_text())
    board = design["projects"]["board"]
    project = json.loads((ROOT / "chess-board.kicad_pro").read_text())
    settings = project["board"]["design_settings"]
    report_path = ROOT / "generated/drc.json"
    report = json.loads(report_path.read_text()) if report_path.is_file() else {}
    erc_path = ROOT / "generated/erc.json"
    erc = json.loads(erc_path.read_text()) if erc_path.is_file() else {}

    unknown = sorted(
        {
            component.get("part_key", "<missing>")
            for component in board["components"].values()
        }
        - set(COMPONENTS)
    )
    mismatches = sorted(
        reference
        for reference, component in board["components"].items()
        if component.get("part_key") in COMPONENTS
        and component["package"] != COMPONENTS[component["part_key"]].package
    )
    implicit_nc = sum(
        len(connection["pads"]) == 1 and not connection.get("no_connect", False)
        for connection in board["connections"]
    )
    ignored = sorted(
        name
        for name, severity in settings.get("rule_severities", {}).items()
        if severity == "ignore"
    )

    result = {
        "schema": 1,
        "revision": board.get("revision"),
        "components": len(board["components"]),
        "approved_products": len(COMPONENTS),
        "connections": len(board["connections"]),
        "explicit_no_connects": sum(
            bool(connection.get("no_connect")) for connection in board["connections"]
        ),
        "unknown_part_keys": unknown,
        "package_mismatches": mismatches,
        "implicit_no_connects": implicit_nc,
        "bom_current": (ROOT / "design/bom.md").read_text() == render_bom(),
        "native_schematic": (ROOT / "chess-board.kicad_sch").is_file(),
        "drc_exclusions": len(settings.get("drc_exclusions", [])),
        "ignored_drc_rules": ignored,
        "erc_violations": sum(
            len(sheet.get("violations", [])) for sheet in erc.get("sheets", [])
        ),
        "drc_violations": len(report.get("violations", [])),
        "unconnected_items": len(report.get("unconnected_items", [])),
        "schematic_parity_errors": len(report.get("schematic_parity", [])),
        "prototype_records": len(
            [
                path
                for path in (ROOT / "prototype").glob("*")
                if path.name != "README.md"
            ]
        ),
    }
    result["release_ready"] = all(
        (
            not unknown,
            not mismatches,
            implicit_nc == 0,
            result["bom_current"],
            result["native_schematic"],
            result["drc_exclusions"] == 0,
            not ignored,
            result["erc_violations"] == 0,
            result["drc_violations"] == 0,
            result["unconnected_items"] == 0,
            result["schematic_parity_errors"] == 0,
            result["prototype_records"] > 0,
        )
    )
    return result


def main() -> None:
    result = audit()
    destination = ROOT / "generated/audit.json"
    destination.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(f"wrote {destination}")
    print(
        "release ready" if result["release_ready"] else
        f"release blocked: {result['unconnected_items']} open, "
        f"schematic={result['native_schematic']}, "
        f"prototype records={result['prototype_records']}"
    )


if __name__ == "__main__":
    main()
