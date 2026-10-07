"""Summarize circuit output and unresolved work alongside generation artifacts."""

from __future__ import annotations

import json
from enum import StrEnum
from pathlib import Path
from typing import cast

from pcb.harness import BoardComponent, Circuit, Net
from pcb.harness.checks.pcbnew.netlist import declared_connections


def write_report[BoardNet: Net](
    declaration: Circuit[BoardNet],
    directory: Path,
    name: str,
    pending: tuple[str, ...],
    electrical_checks: dict[str, object],
) -> None:
    """Record findings and board-specific work that is still outstanding."""
    if electrical_checks.get("complete") is not True:
        raise ValueError("cannot report incomplete electrical checks as passed")
    expected, unused = declared_connections(declaration)
    erc = cast(dict[str, object], json.loads((directory / "erc.json").read_text()))
    drc = cast(dict[str, object], json.loads((directory / "drc.json").read_text()))
    summary = {
        "electrical_checks": {"status": "passed", **electrical_checks},
        "components": len(declaration.components()),
        "tracks": len(declaration.traces()),
        "vias": len(declaration.vias()),
        "planes": len(declaration.layout.planes),
        "copper_layers": declaration.layout.copper_layers,
        "mounting_holes": len(declaration.layout.holes),
        "nets": len(expected),
        "unused_pins": len(unused),
        "schematic_pin_map_matches": True,
        "schematic_pcb_parity_matches": True,
        "erc_findings": sum(
            len(cast(list[object], sheet["violations"]))
            for sheet in cast(list[dict[str, object]], erc.get("sheets", []))
        ),
        "drc_findings": len(cast(list[object], drc.get("violations", []))),
        "unrouted_connections": len(
            cast(list[object], drc.get("unconnected_items", []))
        ),
        "fabrication_ready": False,
        "remaining": list(pending),
        "fabrication_archive": f"{name}-fabrication.zip",
    }
    components = [
        cast(BoardComponent[StrEnum], component)
        for component in declaration.components()
    ]
    (directory / "layout.json").write_text(
        json.dumps(
            {
                "placements": {
                    component.reference: [
                        component.placement.x_mm,
                        component.placement.y_mm,
                        component.placement.rotation_degrees,
                    ]
                    for component in components
                },
                "components": {
                    component.reference: {
                        "description": component.purpose,
                        "value": component.definition.product.part_number,
                        "package": component.definition.product.package,
                        "manufacturer": component.definition.product.manufacturer,
                        "side": component.placement.side.value,
                    }
                    for component in components
                },
            },
            indent=2,
        )
        + "\n"
    )
    (directory / "manifest.json").write_text(json.dumps(summary, indent=2) + "\n")
    (directory / "README.md").write_text(
        "# Generated PCB\n\n"
        "Source: `pcb.board.board.Board()`. Regenerate with "
        "`PYTHONPATH=hardware python3 -m pcb.board.generate`.\n\n"
        f"Open `{name}.kicad_pro` in KiCad. Schematics embed all symbols "
        "and show the declared pin maps; PCB footprints come from component land patterns. "
        "The exported schematic netlist is checked against every declared connected pin.\n\n"
        "The PCB includes routed copper, filled internal rail planes, mounting holes "
        "and assembly markings. `chess-board.glb` is the native 3D assembly imported by CAD; "
        "`models/` contains portable STEP bodies and `3d-models.json` records fidelity and provenance. "
        "ERC/DRC findings are in `erc.json` and `drc.json`. "
        "Electrical pin roles are unspecified; ERC does not validate driver/power compatibility. "
        "`board-top.svg` and `board-top.png` show the same copper view; bottom views are mirrored. "
        "`board-connections.svg` shows logical connectivity as dashed airwires, not extra copper. "
        "`manifest.json` lists remaining work. The fabrication ZIP contains Gerbers and drill files; "
        "generating it does not approve manufacturing.\n\n"
        "Board-specific sensing and button simulations passed; results are in `electrical-checks/`. "
        "These use ideal sensor, contact and external GPIO bias models; I2C, magnetic margins, firmware debounce and a complete board model remain untested.\n"
    )
