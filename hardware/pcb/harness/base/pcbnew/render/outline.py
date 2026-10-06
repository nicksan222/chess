"""Turn a rectangular outline declaration into native edge graphics.

KiCad recognises board boundaries from graphics on ``Edge.Cuts``. The
renderer therefore emits four ``PCB_SHAPE`` line segments, rather than a
separate Python rectangle object or a manufacturing file. The rectangle is
centred in harness coordinates and converted through :func:`native_point`.
"""

from __future__ import annotations

import pcbnew

from ..outline import BoardOutline
from ..point import Point
from .units import native_point


def render_outline(board: pcbnew.BOARD, outline: BoardOutline) -> None:
    """Add four closed ``Edge.Cuts`` segments around the declared board area.

    Each pair of neighbouring corners becomes one native segment with a
    0.05 mm graphic width. The function establishes the visible boundary;
    KiCad's board parser/DRC still decides whether the saved outline is valid
    for manufacturing, and this function cannot express cut-outs or arcs.
    """
    x, y = outline.width_mm / 2, outline.height_mm / 2
    corners = (Point(-x, y), Point(x, y), Point(x, -y), Point(-x, -y))
    for start, end in zip(corners, corners[1:] + corners[:1]):
        edge = pcbnew.PCB_SHAPE(board)
        edge.SetShape(pcbnew.SHAPE_T_SEGMENT)
        edge.SetStart(native_point(start, outline))
        edge.SetEnd(native_point(end, outline))
        edge.SetLayer(pcbnew.Edge_Cuts)
        edge.SetWidth(pcbnew.FromMM(0.05))
        board.Add(edge)
