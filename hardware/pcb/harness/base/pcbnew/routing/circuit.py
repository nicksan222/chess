"""Turn a native routing pass into typed copper owned by the circuit."""

from collections.abc import Callable
from enum import StrEnum
from typing import cast

import pcbnew

from ...circuit import Circuit
from ...component import BoardComponent
from ...net import Net
from ..point import Point
from ..render.board import render_board
from ..render.route import LAYER_IDS
from ..route import Trace, Via


def route_circuit[BoardNet: Net](
    circuit: Circuit[BoardNet], router: Callable[[pcbnew.BOARD], None]
) -> None:
    if circuit.traces() or circuit.vias():
        raise ValueError("route the circuit once before adding manual copper")
    outline = circuit.outline
    if outline is None:
        raise ValueError("routing requires a board outline")
    board = render_board(circuit)
    for part in circuit.components():
        footprint = board.FindFootprintByReference(part.reference)
        if footprint is None:
            raise ValueError(f"missing {part.reference}")
        footprint.SetValue(
            cast(BoardComponent[StrEnum], part).definition.product.part_number
        )
    router(board)
    layers = {number: layer for layer, number in LAYER_IDS.items()}
    nets: dict[str, BoardNet] = {
        net.label: cast(BoardNet, net) for net in circuit.net_type
    }

    def point(at: pcbnew.VECTOR2I) -> Point:
        return Point(
            pcbnew.ToMM(at.x) - outline.width_mm / 2,
            outline.height_mm / 2 - pcbnew.ToMM(at.y),
        )

    # Collect before mutating the circuit: a failed conversion leaves it untouched.
    traces: list[Trace[BoardNet]] = []
    vias: list[Via[BoardNet]] = []
    for item in board.GetTracks():
        net = nets[item.GetNetname()]
        if isinstance(item, pcbnew.PCB_VIA):
            vias.append(
                Via(
                    net,
                    point(item.GetPosition()),
                    pcbnew.ToMM(item.GetWidth(pcbnew.F_Cu)),
                    pcbnew.ToMM(item.GetDrillValue()),
                )
            )
        else:
            traces.append(
                Trace(
                    net,
                    point(item.GetStart()),
                    point(item.GetEnd()),
                    layers[item.GetLayer()],
                    pcbnew.ToMM(item.GetWidth()),
                )
            )
    for trace in traces:
        circuit.trace(trace)
    for via in vias:
        circuit.via(via)
