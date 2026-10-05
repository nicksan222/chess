"""Read this first: native KiCad board construction from typed subsystem ports."""

from __future__ import annotations

import pcbnew

from pcb.definition.native import (
    add_mechanical_features,
    connections,
    new_board,
    parts,
)
from pcb.definition.validation import validate
from shared import dimensions


def load() -> pcbnew.BOARD:
    from pcb.definition.assemblies import controls, power, sensing, square

    board = new_board()
    power.add_power(board)
    controls.add_controls(board)
    squares = {
        board_square.name: square.add_square(board, board_square=board_square)
        for board_square in dimensions.BOARD_SQUARES
    }
    sensing.add_sensor_banks(board, squares=squares)
    square.connect_led_chain(board, squares)
    add_mechanical_features(board)
    validate(board)
    return board


def netlist(board: pcbnew.BOARD | None = None) -> dict[str, object]:
    """Expanded output derived from native fields and actual pad-to-net assignment."""
    board = board if board is not None else load()
    graph = connections(board)
    return {
        "title": board.GetTitleBlock().GetTitle(),
        "revision": board.GetTitleBlock().GetRevision(),
        "components": {
            f.GetReference(): {
                "part_key": f.GetFieldText("PartKey"),
                "package": f.GetFieldText("Package"),
                "lib": f.GetFieldText("Library"),
                "value": f.GetFieldText("NominalValue"),
                "description": f.GetFieldText("Purpose"),
                "assembly": f.GetFieldText("Assembly"),
                "extras": {
                    k: v
                    for k, v in f.GetFieldsText().items()
                    if k
                    in (
                        "Square",
                        "ChainIndex",
                        "Sensor",
                        "Bank",
                        "Address",
                        "For",
                        "Function",
                    )
                },
            }
            for f in parts(board)
        },
        "connections": [
            {
                "name": name,
                "pads": [list(e) for e in nodes],
                **({"no_connect": True} if name.startswith("unconnected-") else {}),
            }
            for name, nodes in graph.items()
        ],
        "nets": {
            name: [list(e) for e in nodes]
            for name, nodes in graph.items()
            if not name.startswith("unconnected-")
        },
    }
