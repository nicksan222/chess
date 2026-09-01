#!/usr/bin/env python3
"""Generate the native KiCad board from reusable object-oriented stages."""

from __future__ import annotations

import sys
from pathlib import Path

PCB_ROOT = Path(__file__).resolve().parent
HARDWARE_ROOT = PCB_ROOT.parent
sys.path.insert(0, str(PCB_ROOT))
sys.path.insert(0, str(HARDWARE_ROOT))

from base.kicad import board as kicad
from board import definition
from board.wiring import geometry as board_builder
from board.wiring import router

GENERATED = PCB_ROOT / "generated"
BOARD_PATH = GENERATED / "chess-board.kicad_pcb"
DSN_PATH = GENERATED / "chess-board.dsn"


class ChessBoardProject:
    """Compose, route, and save one complete native KiCad project board."""

    def __init__(self) -> None:
        self.design = definition.load()
        self.layout = kicad.KiCadBoard(self.design)
        self.geometry = board_builder.BoardGeometry(self.layout)
        self.writer = board_builder.NativeBoardWriter(self.layout)

    def compose(self) -> None:
        for component in self.design.components.values():
            self.layout.attach(component)
        self.geometry.add_mechanical_features()

    def route(self) -> None:
        router.ChessBoardRouter(self.layout).route()
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
