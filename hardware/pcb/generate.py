#!/usr/bin/env python3
"""Generate the native KiCad board from reusable object-oriented stages."""

from __future__ import annotations

import sys
from pathlib import Path

PCB_ROOT = Path(__file__).resolve().parent
HARDWARE_ROOT = PCB_ROOT.parent
sys.path.insert(0, str(PCB_ROOT))
sys.path.insert(0, str(HARDWARE_ROOT))

from core import (  # noqa: E402
    board_builder,
    connectivity,
    kicad,
    placement,
    routing,
    sources,
)

GENERATED = PCB_ROOT / "generated"
BOARD_PATH = GENERATED / "chess-board.kicad_pcb"
DSN_PATH = GENERATED / "chess-board.dsn"


class ChessBoardProject:
    """Compose, route, and save one complete native KiCad project board."""

    def __init__(self) -> None:
        self.contract = sources.netlist()
        self.placements = placement.build()
        self.connections = connectivity.ConnectionGraph.from_contract(
            self.contract["connections"],
            self.placements,
        )
        self.layout = kicad.KiCadBoard(self.connections)
        self.geometry = board_builder.BoardGeometry(self.layout)
        self.writer = board_builder.NativeBoardWriter(self.layout)

    def compose(self) -> None:
        components = self.contract["components"]
        for item in self.placements:
            item.attach_to(self.layout, components[item.reference])
        self.geometry.add_mechanical_features()

    def route(self) -> None:
        routing.ChessBoardRouter(self.layout).route()
        self.geometry.add_power_planes()

    def write(self) -> None:
        self.writer.write(BOARD_PATH, DSN_PATH)
        print(f"wrote {BOARD_PATH}")
        print(f"wrote {DSN_PATH}")

    def build(self) -> None:
        self.compose()
        self.route()
        self.write()


if __name__ == "__main__":
    ChessBoardProject().build()
