"""Read this first: native KiCad board construction from typed subsystem ports.

Role: the top of the PCB pipeline. `load()` composes the whole board by asking each
assembly (power, controls, one per square, Hall banks, LED chain) to place its
footprints and assign nets on a fresh `pcbnew.BOARD`, then validates it. `build.py`
calls `load()` and then routes/exports the result; everything downstream (netlist,
BOM, schematic) is derived from the board returned here, not from a second model.
"""

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
    """Build and validate the complete (unrouted) board from the shared contracts.

    The order matters only where one assembly needs handles from another: squares
    must exist before the Hall banks (`sensing`) can connect each square's sensor,
    and before the LED chain can link neighbouring squares.
    """
    # Imported lazily so merely importing `board` (e.g. for `netlist`'s type)
    # does not pull in every assembly and the pcbnew footprint templates.
    from pcb.definition.assemblies import controls, power, sensing, square

    board = new_board()
    power.add_power(board)
    controls.add_controls(board)
    # One handle per square, keyed by name ("E4"), so later steps address squares
    # through the shared layout instead of searching footprints.
    squares = {
        board_square.name: square.add_square(board, board_square=board_square)
        for board_square in dimensions.BOARD_SQUARES
    }
    sensing.add_sensor_banks(board, squares=squares)
    square.connect_led_chain(board, squares)
    add_mechanical_features(board)
    # Last, so it checks the finished board: approved products, complete pad
    # assignment, square centres and Hall-bank wiring.
    validate(board)
    return board


def netlist(board: pcbnew.BOARD | None = None) -> dict[str, object]:
    """Expanded output derived from native fields and actual pad-to-net assignment.

    Written to `generated/netlist.json`. It is not a design input (nothing
    regenerates the board from it), but tests and review reports read it. Reading
    connectivity from the pads themselves means the netlist cannot disagree with the board. Nets named `unconnected-*` are KiCad's placeholders for
    pads deliberately marked no-connect, so they are listed as connections flagged
    `no_connect` but excluded from `nets`.
    """
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
                # Selected per-footprint fields that carry design intent (square,
                # LED chain slot, Hall sensor number, bank/address, capacitor target).
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
