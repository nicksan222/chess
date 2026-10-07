"""Fill declared copper planes on the final saved board."""

from pathlib import Path

import pcbnew

from .identity import normalize_board_uuids


def fill_planes(path: Path) -> None:
    board = pcbnew.LoadBoard(str(path))
    pcbnew.ZONE_FILLER(board).Fill(board.Zones())
    if not pcbnew.SaveBoard(str(path), board):
        raise OSError(f"could not save filled board: {path}")
    normalize_board_uuids(board, path)
