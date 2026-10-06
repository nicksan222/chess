"""Create a small KiCad board project from a declarative circuit.

The project contains a ``.kicad_pro`` settings file and a matching
``.kicad_pcb`` board. It intentionally contains no inferred schematic: a
schematic needs symbol and circuit intent beyond package pad geometry.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import cast

import pcbnew

from ...circuit import Circuit
from ...net import Net
from .board import render_board
from .identity import normalize_board_uuids


def write_project[BoardNet: Net](
    circuit: Circuit[BoardNet], directory: Path, name: str
) -> Path:
    """Create a fresh, matching KiCad project and board without overwriting.

    Validate and render before creating the directory. A failed KiCad save
    removes only the files and directory this function just created.
    """
    if not isinstance(cast(object, name), str) or not re.fullmatch(
        r"[A-Za-z][A-Za-z0-9_-]*", name
    ):
        raise ValueError("project name must be a simple letter-led identifier")
    board = render_board(circuit)
    directory.mkdir(parents=True)
    project_path = directory / f"{name}.kicad_pro"
    board_path = directory / f"{name}.kicad_pcb"
    local_state_path = directory / f"{name}.kicad_prl"
    try:
        if not pcbnew.SaveBoard(str(board_path), board):
            raise OSError(f"could not write KiCad board: {board_path}")
        normalize_board_uuids(board, board_path)
        if not project_path.is_file():
            raise OSError(f"KiCad did not write project settings: {project_path}")
    except Exception:
        board_path.unlink(missing_ok=True)
        project_path.unlink(missing_ok=True)
        local_state_path.unlink(missing_ok=True)
        directory.rmdir()
        raise
    # KiCad also writes per-user editor state. It is not part of a portable
    # project and should never be checked in alongside the reviewed design.
    local_state_path.unlink(missing_ok=True)
    return project_path
