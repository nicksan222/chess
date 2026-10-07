"""Materialise stackup, planes, mounting holes and silkscreen declarations."""

import math

import pcbnew

from ...net import Net
from ..layout import BoardLayout
from ..outline import BoardOutline
from ..point import Point
from .route import LAYER_IDS
from .units import native_point


def configure_board[BoardNet: Net](
    board: pcbnew.BOARD, layout: BoardLayout[BoardNet]
) -> None:
    if layout.copper_layers not in (2, 4, 6, 8):
        raise ValueError("supported copper layer counts are 2, 4, 6 and 8")
    for dimension in (
        layout.thickness_mm,
        layout.minimum_clearance_mm,
        layout.minimum_track_width_mm,
        layout.edge_clearance_mm,
    ):
        if dimension is not None and (not math.isfinite(dimension) or dimension <= 0):
            raise ValueError("layout dimensions must be finite and positive")
    board.SetCopperLayerCount(layout.copper_layers)
    settings = board.GetDesignSettings()
    settings.SetBoardThickness(pcbnew.FromMM(layout.thickness_mm))
    if layout.minimum_clearance_mm is not None:
        settings.m_MinClearance = pcbnew.FromMM(layout.minimum_clearance_mm)
    if layout.minimum_track_width_mm is not None:
        settings.m_TrackMinWidth = pcbnew.FromMM(layout.minimum_track_width_mm)
    if layout.edge_clearance_mm is not None:
        settings.m_CopperEdgeClearance = pcbnew.FromMM(layout.edge_clearance_mm)


def render_layout[BoardNet: Net](
    board: pcbnew.BOARD, layout: BoardLayout[BoardNet], outline: BoardOutline
) -> None:
    references = {footprint.GetReference() for footprint in board.GetFootprints()}
    for hole in layout.holes:
        if not hole.reference or hole.reference in references:
            raise ValueError("mounting holes require unique references")
        references.add(hole.reference)
        if not math.isfinite(hole.diameter_mm):
            raise ValueError("mounting hole diameter must be finite")
        if (
            hole.diameter_mm <= 0
            or abs(hole.center.x_mm) + hole.diameter_mm / 2 >= outline.width_mm / 2
            or abs(hole.center.y_mm) + hole.diameter_mm / 2 >= outline.height_mm / 2
        ):
            raise ValueError("mounting hole must lie inside the board")
        footprint = pcbnew.FOOTPRINT(board)
        footprint.SetReference(hole.reference)
        footprint.SetValue("Mounting hole")
        footprint.SetPosition(native_point(hole.center, outline))
        footprint.SetBoardOnly(True)
        footprint.SetExcludedFromBOM(True)
        footprint.SetExcludedFromPosFiles(True)
        footprint.Reference().SetVisible(False)
        footprint.Value().SetVisible(False)
        pad = pcbnew.PAD(footprint)
        pad.SetPosition(footprint.GetPosition())
        diameter = pcbnew.FromMM(hole.diameter_mm)
        pad.SetSize(pcbnew.VECTOR2I(diameter, diameter))
        pad.SetDrillSize(pcbnew.VECTOR2I(diameter, diameter))
        pad.SetShape(pcbnew.PAD_SHAPE_CIRCLE)
        pad.SetAttribute(pcbnew.PAD_ATTRIB_NPTH)
        pad.SetLayerSet(pad.UnplatedHoleMask())
        footprint.Add(pad)
        board.Add(footprint)
    for label in layout.labels:
        if not label.text or any(
            not math.isfinite(value) or value <= 0
            for value in (label.height_mm, label.width_mm)
        ):
            raise ValueError("labels need text and positive dimensions")
        text = pcbnew.PCB_TEXT(board)
        text.SetText(label.text)
        text.SetPosition(native_point(label.center, outline))
        text.SetLayer(pcbnew.F_SilkS)
        height = pcbnew.FromMM(label.height_mm)
        text.SetTextSize(pcbnew.VECTOR2I(height, height))
        text.SetTextThickness(pcbnew.FromMM(label.width_mm))
        board.Add(text)
    for line in layout.lines:
        if (
            line.start == line.end
            or not math.isfinite(line.width_mm)
            or line.width_mm <= 0
        ):
            raise ValueError(
                "silkscreen lines need distinct endpoints and positive width"
            )
        shape = pcbnew.PCB_SHAPE(board)
        shape.SetShape(pcbnew.SHAPE_T_SEGMENT)
        shape.SetStart(native_point(line.start, outline))
        shape.SetEnd(native_point(line.end, outline))
        shape.SetWidth(pcbnew.FromMM(line.width_mm))
        shape.SetLayer(pcbnew.F_SilkS)
        board.Add(shape)
    for plane in layout.planes:
        if (
            not 0 < plane.inset_mm < min(outline.width_mm, outline.height_mm) / 2
            or not math.isfinite(plane.clearance_mm)
            or plane.clearance_mm <= 0
        ):
            raise ValueError("plane inset and clearance must fit the board")
        zone = pcbnew.ZONE(board)
        net = board.FindNet(plane.net.label)
        if net is None:
            raise ValueError(f"plane has no component connection: {plane.net.label}")
        zone.SetNet(net)
        zone.SetLayer(LAYER_IDS[plane.layer])
        zone.SetLocalClearance(pcbnew.FromMM(plane.clearance_mm))
        x = outline.width_mm / 2 - plane.inset_mm
        y = outline.height_mm / 2 - plane.inset_mm
        zone.Outline().NewOutline()
        for point in (Point(-x, -y), Point(x, -y), Point(x, y), Point(-x, y)):
            position = native_point(point, outline)
            zone.Outline().Append(position.x, position.y)
        board.Add(zone)
