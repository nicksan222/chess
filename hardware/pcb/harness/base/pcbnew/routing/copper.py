"""Native copper primitives shared by exact escapes and grid paths."""

from typing import TypedDict, Unpack

import pcbnew


class TraceStyle(TypedDict, total=False):
    """Optional `add_trace` keywords: copper layer id and width in millimetres."""

    layer: int
    width: float


def add_trace(
    board: pcbnew.BOARD,
    net: pcbnew.NETINFO_ITEM,
    start: pcbnew.VECTOR2I,
    end: pcbnew.VECTOR2I,
    **style: Unpack[TraceStyle],
) -> None:
    layer = style.get("layer", pcbnew.F_Cu)
    width = style.get("width", 0.31)
    if start == end:
        return
    trace = pcbnew.PCB_TRACK(board)
    trace.SetStart(start)
    trace.SetEnd(end)
    trace.SetWidth(pcbnew.FromMM(width))
    trace.SetLayer(layer)
    trace.SetNet(net)
    board.Add(trace)


def add_via(
    board: pcbnew.BOARD,
    net: pcbnew.NETINFO_ITEM,
    at: pcbnew.VECTOR2I,
    diameter_mm: float = 0.9,
    drill_mm: float = 0.4,
) -> None:
    via = pcbnew.PCB_VIA(board)
    via.SetPosition(at)
    via.SetWidth(pcbnew.FromMM(diameter_mm))
    via.SetDrill(pcbnew.FromMM(drill_mm))
    via.SetNet(net)
    board.Add(via)
