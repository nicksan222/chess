#!/usr/bin/env python3
"""Compose the native KiCad schematic from reviewed connectivity and products."""

from __future__ import annotations

import sys
from pathlib import Path

PCB_ROOT = Path(__file__).resolve().parents[1]
HARDWARE_ROOT = PCB_ROOT.parent
sys.path[:0] = [str(PCB_ROOT), str(HARDWARE_ROOT)]

from board import artifacts
from board import definition as board_definition
from domain.design import BoardDesign
from domain.schematic import (
    SYMBOL_COLUMN_PITCH_MM,
    SYMBOL_COLUMNS,
    SYMBOL_ROW_GAP_MM,
    EndpointKey,
    connectivity,
    row_centres,
)
from domain.schematic import (
    render as render_design,
)
from domain.schematic_symbols import (
    NAMESPACE,
    ROOT_UUID,
    render_symbol_library,
    uid,
)

# Preserve the original module entry points while implementations live nearby.
__all__ = [
    "NAMESPACE",
    "ROOT_UUID",
    "SYMBOL_COLUMNS",
    "SYMBOL_COLUMN_PITCH_MM",
    "SYMBOL_ROW_GAP_MM",
    "EndpointKey",
    "connectivity",
    "render",
    "render_symbol_library",
    "row_centres",
    "uid",
    "write",
]


def render(design: BoardDesign | None = None) -> str:
    """Keep the script API's default design while the renderer stays reusable."""
    return render_design(design or board_definition.load())


def write() -> None:
    artifacts.GENERATED_DIR.mkdir(exist_ok=True)
    schematic = render()
    artifacts.SCHEMATIC.write_text(schematic)
    artifacts.SYMBOL_LIBRARY.write_text(render_symbol_library(schematic))
    artifacts.SYMBOL_TABLE.write_text(
        "(sym_lib_table\n"
        "  (version 7)\n"
        '  (lib (name "Generated")(type "KiCad")'
        '(uri "${KIPRJMOD}/generated-symbols.kicad_sym")(options "")(descr ""))\n'
        ")\n"
    )
    print(f"wrote {artifacts.SCHEMATIC}")
    print(f"wrote {artifacts.SYMBOL_LIBRARY}")


if __name__ == "__main__":
    write()
