"""Canonical paths for generated files belonging to this board project."""

from pathlib import Path

PCB_ROOT = Path(__file__).resolve().parents[1]
GENERATED_DIR = PCB_ROOT / "generated"

BOARD = GENERATED_DIR / "chess-board.kicad_pcb"
DSN = GENERATED_DIR / "chess-board.dsn"
PROJECT = GENERATED_DIR / "chess-board.kicad_pro"
SCHEMATIC = GENERATED_DIR / "chess-board.kicad_sch"
SYMBOL_LIBRARY = GENERATED_DIR / "generated-symbols.kicad_sym"
SYMBOL_TABLE = GENERATED_DIR / "sym-lib-table"
BOM = GENERATED_DIR / "bom.md"
ASSEMBLY_BOM = GENERATED_DIR / "assembly-bom.csv"
BOARD_TOP_SVG = GENERATED_DIR / "board-top.svg"
BOARD_BOTTOM_SVG = GENERATED_DIR / "board-bottom.svg"
