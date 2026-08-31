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

import footprints  # noqa: E402
from components.catalog import for_netlist_entry, known_part_keys  # noqa: E402
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
    anonymous_products = sorted(
        reference
        for reference, component in board["components"].items()
        if component.get("part_key") in COMPONENTS
        and (
            not COMPONENTS[component["part_key"]].manufacturer.strip()
            or not COMPONENTS[component["part_key"]].mpn.strip()
            or COMPONENTS[component["part_key"]].manufacturer.casefold() == "generic"
            or COMPONENTS[component["part_key"]].mpn
            == COMPONENTS[component["part_key"]].key
        )
    )
    used_part_keys = {
        component.get("part_key", "<missing>")
        for component in board["components"].values()
    }
    missing_models = sorted(used_part_keys - known_part_keys())
    pin_model_mismatches = []
    for reference, component in board["components"].items():
        if component.get("part_key") in missing_models:
            continue
        if component.get("package") not in footprints.CATALOG:
            pin_model_mismatches.append(reference)
            continue
        model = for_netlist_entry(reference, component)
        footprint = footprints.for_package(component["package"])
        if {pad.net_number for pad in footprint.pads} != set(model.get_pins()):
            pin_model_mismatches.append(reference)

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
        "anonymous_products": anonymous_products,
        "missing_component_models": missing_models,
        "pin_model_mismatches": pin_model_mismatches,
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
            not anonymous_products,
            not missing_models,
            not pin_model_mismatches,
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
