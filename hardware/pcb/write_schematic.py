#!/usr/bin/env python3
"""Compose the native KiCad schematic from reviewed connectivity and products."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
HARDWARE = ROOT.parent
sys.path[:0] = [str(ROOT), str(HARDWARE)]

from base.design import BoardDesign
from base.schematic import (
    SYMBOL_COLUMN_PITCH_MM,
    SYMBOL_COLUMNS,
    SYMBOL_ROW_GAP_MM,
    EndpointKey,
    connectivity,
    row_centres,
)
from base.schematic import (
    render as render_design,
)
from base.schematic_symbols import (
    NAMESPACE,
    ROOT_UUID,
    render_symbol_library,
    uid,
)
from board import artifacts
from board import definition as board_definition

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
