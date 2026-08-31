#!/usr/bin/env python3
"""Hard release gates: no exclusions, DRC errors, or missing copper."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PROJECT = ROOT / "chess-board.kicad_pro"
CONNECTIVITY = ROOT / "design" / "netlist.json"
SCHEMATIC = ROOT / "chess-board.kicad_sch"
REPORT = ROOT / "generated" / "drc.json"
ERC_REPORT = ROOT / "generated" / "erc.json"
BOM = ROOT / "design" / "bom.md"


def validate() -> None:
    prototype_records = [
        path for path in (ROOT / "prototype").glob("*")
        if path.name != "README.md"
    ]
    if not prototype_records:
        raise SystemExit("release blocked: reed/magnet prototype evidence is missing")

    if not SCHEMATIC.is_file():
        raise SystemExit("release blocked: native KiCad schematic is missing")

    project = json.loads(PROJECT.read_text())
    settings = project.get("board", {}).get("design_settings", {})
    exclusions = settings.get("drc_exclusions", [])
    if exclusions:
        raise SystemExit(f"release blocked: {len(exclusions)} DRC exclusions")
    ignored = sorted(
        name for name, severity in settings.get("rule_severities", {}).items()
        if severity == "ignore"
    )
    if ignored:
        raise SystemExit(f"release blocked: ignored DRC rules: {', '.join(ignored)}")

    from write_bom import render as render_bom

    expected_bom = render_bom()
    if BOM.read_text() != expected_bom:
        raise SystemExit("release blocked: approved BOM is stale; run write_bom.py")

    source = json.loads(CONNECTIVITY.read_text())["projects"]["board"]
    for index, connection in enumerate(source["connections"], 1):
        pads = connection["pads"]
        explicit = connection.get("no_connect", False)
        if len(pads) == 1 and not explicit:
            raise SystemExit(f"connection {index} is silently unconnected")
        if len(pads) != 1 and explicit:
            raise SystemExit(f"connection {index} incorrectly bypasses routing")

    erc = json.loads(ERC_REPORT.read_text())
    erc_violations = sum(
        len(sheet.get("violations", [])) for sheet in erc.get("sheets", [])
    )
    if erc_violations:
        raise SystemExit(f"release blocked: {erc_violations} ERC violations")

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

    from audit import audit

    completeness = audit()
    product_failures = {
        key: completeness[key]
        for key in (
            "unknown_part_keys",
            "package_mismatches",
            "anonymous_products",
            "missing_component_models",
            "pin_model_mismatches",
        )
        if completeness[key]
    }
    if product_failures:
        raise SystemExit(
            "release blocked: product-model audit failed: "
            f"{json.dumps(product_failures, sort_keys=True)}"
        )
    print(
        "PCB release gate passed: exact products, typed pins, footprints, "
        "connectivity, ERC, and DRC agree"
    )


if __name__ == "__main__":
    validate()
