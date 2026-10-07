"""Write KiCad projects from harness circuit declarations.

``write_project`` exports a PCB-only project. ``write_schematic_project``
exports linked PCB and embedded connection schematics into an empty staging
directory; callers own publication and rollback of the complete artifact set.
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


def write_schematic_project[BoardNet: Net](
    circuit: Circuit[BoardNet], directory: Path, name: str
) -> Path:
    """Write linked PCB/schematic files into an empty staging directory.

    The caller owns publication and rollback. Unlike ``write_project``, this
    accepts an existing empty directory so atomic output staging needs no
    remove/recreate workaround in the board's generation script.
    """
    from enum import StrEnum

    from ...component import BoardComponent
    from .schematic import write_schematic

    if not re.fullmatch(r"[A-Za-z][A-Za-z0-9_-]*", name):
        raise ValueError("project name must be a simple letter-led identifier")
    if directory.exists() and any(directory.iterdir()):
        raise FileExistsError(f"project directory must be empty: {directory}")
    board = render_board(circuit)
    directory.mkdir(parents=True, exist_ok=True)
    schematics = write_schematic(circuit, directory, name)
    products = {
        part.reference: cast(BoardComponent[StrEnum], part).definition.product
        for part in circuit.components()
    }
    for footprint in board.GetFootprints():
        reference = footprint.GetReference()
        if reference not in products:
            continue
        footprint.SetValue(products[reference].part_number)
        footprint.SetPath(pcbnew.KIID_PATH(schematics.symbol_paths[reference]))
    board_path = directory / f"{name}.kicad_pcb"
    project_path = directory / f"{name}.kicad_pro"
    if not pcbnew.SaveBoard(str(board_path), board):
        raise OSError(f"could not write KiCad board: {board_path}")
    normalize_board_uuids(board, board_path)
    if not project_path.is_file():
        raise OSError(f"KiCad did not write project settings: {project_path}")
    (directory / f"{name}.kicad_prl").unlink(missing_ok=True)
    return project_path
