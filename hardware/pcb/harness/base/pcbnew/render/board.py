"""Assemble a complete native KiCad board from one typed circuit.

This is the top-level adapter from harness vocabulary to ``pcbnew`` objects:
outline segments, named ``NETINFO_ITEM`` records, footprints/pads, tracks, and
vias. The circuit remains the declarative input; the returned ``pcbnew.BOARD``
is the native design that KiCad can open and check.
"""

from __future__ import annotations

from enum import StrEnum
from pathlib import Path
from typing import cast

import pcbnew

from ...circuit import Circuit
from ...component import BoardComponent
from ...connections import NetConnection
from ...net import Net
from .footprint import render_footprint
from .identity import normalize_board_uuids
from .outline import render_outline
from .route import render_trace, render_via


def render_board[BoardNet: Net](circuit: Circuit[BoardNet]) -> pcbnew.BOARD:
    """Build a fresh native board after checking all required physical facts.

    A SPICE-only circuit may omit the physical outline and package land
    patterns. PCB rendering needs both, so this function asks the registry to
    check each courtyard against the edge and neighbouring components before
    creating KiCad objects.
    It then creates the board edge, maps typed design nets to KiCad nets,
    creates footprints, and adds only the traces and vias explicitly declared
    by the circuit. It does not autoroute or run KiCad's design-rule checks.
    Trace width and via diameter must fit within the rectangular board edge.
    This check does not prove that copper meets a pad, joins the intended net,
    clears other copper, or obeys all manufacturing constraints; KiCad DRC
    must inspect the saved board for those properties.
    """
    outline = circuit.outline
    if outline is None:
        raise ValueError("PCB rendering needs a board outline")
    circuit.validate()
    circuit.validate_physical(outline)
    components = circuit.components()
    if any(not isinstance(component, BoardComponent) for component in components):
        raise ValueError("PCB rendering needs BoardComponent instances")
    for component in components:
        part = cast(BoardComponent[StrEnum], component)
        if part.definition.land_pattern is None:
            raise ValueError(f"{part.reference}: no PCB land pattern")
        if not outline.contains(part.placement, part.definition.courtyard):
            raise ValueError(f"{part.reference}: courtyard exceeds board outline")
    declared = {
        connection.net
        for component in components
        for _, connection in component.pin_connections()
        if isinstance(connection, NetConnection)
    }
    if any(route.net not in declared for route in (*circuit.traces(), *circuit.vias())):
        raise ValueError("route net must appear on a component pin")
    for route in circuit.traces():
        radius = route.width_mm / 2
        if any(
            abs(point.x_mm) + radius > outline.width_mm / 2
            or abs(point.y_mm) + radius > outline.height_mm / 2
            for point in (route.start, route.end)
        ):
            raise ValueError("trace copper exceeds board edge")
    for route in circuit.vias():
        radius = route.diameter_mm / 2
        if (
            abs(route.center.x_mm) + radius > outline.width_mm / 2
            or abs(route.center.y_mm) + radius > outline.height_mm / 2
        ):
            raise ValueError("via copper exceeds board edge")
    board = pcbnew.BOARD()
    render_outline(board, outline)
    nets: dict[str, pcbnew.NETINFO_ITEM] = {}
    for name in sorted(declared, key=lambda item: item.label):
        native = pcbnew.NETINFO_ITEM(board, name.label, board.GetNetCount())
        board.Add(native)
        nets[name.label] = native
    for component in components:
        render_footprint(board, cast(BoardComponent[StrEnum], component), outline, nets)
    for route in circuit.traces():
        render_trace(board, route, outline, nets[route.net.label])
    for route in circuit.vias():
        render_via(board, route, outline, nets[route.net.label])
    return board


def write_board[BoardNet: Net](circuit: Circuit[BoardNet], path: Path) -> Path:
    """Render and save a KiCad PCB file, raising if KiCad reports failure.

    The returned path identifies the file written. Saving is not the same as
    opening the file in the KiCad editor, running DRC/ERC, or proving that a
    board can be manufactured. The parent directory must already exist.
    """
    board = render_board(circuit)
    if not pcbnew.SaveBoard(str(path), board):
        raise OSError(f"could not write KiCad board: {path}")
    normalize_board_uuids(board, path)
    return path
