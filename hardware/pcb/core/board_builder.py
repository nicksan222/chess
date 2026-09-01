"""Compose components and mechanical board geometry in KiCad."""

from __future__ import annotations

from pathlib import Path

import pcbnew

from core import kicad, sources
from core.board import Board
from core.nets import Net

BOARD_EDGE_WIDTH_MM = 0.05


class BoardGeometry:
    """Mechanical and plane geometry attached to one native KiCad layout."""

    def __init__(self, layout: kicad.KiCadBoard) -> None:
        self.layout = layout

    def add_mechanical_features(self) -> None:
        _add_outline(self.layout.native)
        _add_mounting_holes(self.layout.native)

    def add_power_planes(self) -> None:
        _add_power_planes(self.layout.native, self.layout.nets)


class NativeBoardWriter:
    """Final native KiCad serialization and router export stage."""

    def __init__(self, layout: kicad.KiCadBoard) -> None:
        self.layout = layout

    def write(self, board_path: Path, dsn_path: Path) -> None:
        _write_board(self.layout.native, board_path, dsn_path)


def _add_mounting_holes(board: pcbnew.BOARD) -> None:
    """Add one plated-copper-free screw clearance over every case boss."""
    shared = sources.dimensions()
    diameter = shared.PCB_MOUNTING_HOLE_DIAMETER_MM
    for index, (x, y) in enumerate(shared.PCB_SUPPORT_POSITIONS_MM, 1):
        module = pcbnew.FOOTPRINT(board)
        module.SetReference(f"H{index}")
        module.SetValue("M3 mounting hole")
        module.SetBoardOnly(True)
        module.Reference().SetVisible(False)
        module.Value().SetVisible(False)
        module.SetPosition(kicad.point(x, y))
        board.Add(module)
        pad = pcbnew.PAD(module)
        pad.SetNumber("")
        pad.SetPosition(kicad.point(x, y))
        pad.SetAttribute(pcbnew.PAD_ATTRIB_NPTH)
        size = pcbnew.FromMM(diameter)
        pad.SetSize(pcbnew.VECTOR2I(size, size))
        pad.SetDrillSize(pcbnew.VECTOR2I(size, size))
        pad.SetShape(pcbnew.PAD_SHAPE_CIRCLE)
        pad.SetLayerSet(pad.UnplatedHoleMask())
        module.Add(pad)
        radius = diameter / 2 + 0.5
        corners = (
            (x - radius, y - radius),
            (x + radius, y - radius),
            (x + radius, y + radius),
            (x - radius, y + radius),
        )
        for corner_index, start in enumerate(corners):
            line = pcbnew.PCB_SHAPE(module)
            line.SetShape(pcbnew.SHAPE_T_SEGMENT)
            line.SetStart(kicad.point(*start))
            line.SetEnd(kicad.point(*corners[(corner_index + 1) % 4]))
            line.SetLayer(pcbnew.F_CrtYd)
            line.SetWidth(pcbnew.FromMM(0.05))
            module.Add(line)


def _add_outline(board: pcbnew.BOARD) -> None:
    dimensions = sources.dimensions()
    width, height, _thickness = dimensions.PCB_SIZE_MM
    x0, x1 = -width / 2, width / 2
    y1 = dimensions.PLAYING_SPAN_MM / 2
    y0 = y1 - height
    corners = ((x0, y0), (x1, y0), (x1, y1), (x0, y1))
    for index, start in enumerate(corners):
        edge = pcbnew.PCB_SHAPE(board)
        edge.SetShape(pcbnew.SHAPE_T_SEGMENT)
        edge.SetStart(kicad.point(*start))
        edge.SetEnd(kicad.point(*corners[(index + 1) % 4]))
        edge.SetLayer(pcbnew.Edge_Cuts)
        edge.SetWidth(pcbnew.FromMM(BOARD_EDGE_WIDTH_MM))
        board.Add(edge)


def _add_power_planes(board, net_by_name) -> None:
    """Add inset ground, 5 V, and 3.3 V zones on dedicated internal layers."""
    envelope = Board()
    corners = (
        (envelope.x_min + 1, envelope.y_min + 1),
        (envelope.x_max - 1, envelope.y_min + 1),
        (envelope.x_max - 1, envelope.y_max - 1),
        (envelope.x_min + 1, envelope.y_max - 1),
    )
    for name, layer in (
        (Net.GROUND, pcbnew.In1_Cu),
        (Net.FIVE_VOLTS, pcbnew.In2_Cu),
        (Net.THREE_VOLTS_THREE, pcbnew.In3_Cu),
    ):
        zone = pcbnew.ZONE(board)
        zone.SetNet(net_by_name[name])
        zone.SetLayer(layer)
        zone.Outline().NewOutline()
        for x, y in corners:
            at = kicad.point(x, y)
            zone.Outline().Append(at.x, at.y)
        board.Add(zone)


def _write_board(
    board: pcbnew.BOARD,
    board_path: Path,
    dsn_path: Path,
) -> None:
    """Fill zones, save the native board, and export its router interchange file."""
    pcbnew.SaveBoard(str(board_path), board)
    filled = pcbnew.LoadBoard(str(board_path))
    pcbnew.ZONE_FILLER(filled).Fill(filled.Zones())
    temporary = board_path.with_suffix(".filled.kicad_pcb")
    pcbnew.SaveBoard(str(temporary), filled)
    temporary.replace(board_path)
    temporary.with_suffix(".kicad_pro").unlink(missing_ok=True)

    filled = pcbnew.LoadBoard(str(board_path))
    dsn_path.parent.mkdir(parents=True, exist_ok=True)
    if not pcbnew.ExportSpecctraDSN(filled, str(dsn_path)):
        raise RuntimeError("KiCad failed to export the autorouter design")
