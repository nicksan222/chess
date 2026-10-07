"""Materialise a placed component declaration as a native KiCad footprint.

The harness keeps a product's pin map and land pattern in ordinary Python
data. This adapter creates one ``pcbnew.FOOTPRINT``, one native ``PAD`` per
land, and four ``PCB_SHAPE`` graphics for its rectangular courtyard. KiCad
then owns the footprint's placement, orientation, side, and native object
identity in the returned board.
"""

from __future__ import annotations

from enum import StrEnum
from typing import cast

import pcbnew

from ...component import BoardComponent
from ...connections import NetConnection, PinConnection
from ...geometry import Side
from ..outline import BoardOutline
from ..pad import PadKind
from ..point import Point
from .pad import render_pad
from .units import native_point


def render_footprint[Pin: StrEnum](
    board: pcbnew.BOARD,
    component: BoardComponent[Pin],
    outline: BoardOutline,
    nets: dict[str, pcbnew.NETINFO_ITEM],
) -> pcbnew.FOOTPRINT:
    """Turn a component declaration into one placed native footprint.

    Each land-pattern pad becomes a native KiCad pad at component centre plus
    its package-local offset. Its logical pin selects the declared net or
    no-connect, and its physical number, shape, size and drill come from the
    pad description. The courtyard is drawn as four footprint-owned lines.
    Bottom-side placement flips the finished footprint across the left/right
    axis at its centre, moving copper to the back face; the final orientation
    sets its rotation around that centre. The package drawing remains the
    source of truth for these measurements.

    The board renderer calls this after creating native nets, so a connected
    pad receives the exact ``NETINFO_ITEM`` selected by its logical net. The
    returned footprint is still only a serialized design object: KiCad DRC is
    responsible for checking clearances and actual copper connectivity.
    """
    pattern = component.definition.land_pattern
    if pattern is None:
        raise ValueError(f"{component.reference}: no PCB land pattern")
    if not outline.contains(component.placement, component.definition.courtyard):
        raise ValueError(f"{component.reference}: courtyard exceeds board outline")
    centre = Point(component.placement.x_mm, component.placement.y_mm)
    native = pcbnew.FOOTPRINT(board)
    native.SetFPID(pcbnew.LIB_ID("", component.definition.product.key))
    kinds = {pad.kind for pad in pattern.pads}
    native.SetAttributes(
        (pcbnew.FP_SMD if PadKind.SURFACE in kinds else 0)
        | (pcbnew.FP_THROUGH_HOLE if PadKind.THROUGH_HOLE in kinds else 0)
    )
    native.SetReference(component.reference)
    native.SetValue(component.definition.product.key)
    # KiCad centres new reference text on the footprint. On small packages it
    # would cross solder pads if left on silkscreen; keep identity on F.Fab
    # until the harness can declare a reviewed silkscreen text location.
    native.Reference().SetLayer(pcbnew.F_Fab)
    native.Value().SetVisible(False)
    native.SetPosition(native_point(centre, outline))
    for pad in pattern.pads:
        connection = cast(PinConnection, component.pins[pad.pin])
        network = (
            nets[connection.net.label]
            if isinstance(connection, NetConnection)
            else None
        )
        render_pad(native, pad, connection, outline, network, centre)
    _courtyard(
        native,
        component.definition.courtyard.width_mm,
        component.definition.courtyard.height_mm,
        centre,
        outline,
    )
    board.Add(native)
    if component.placement.side is Side.BOTTOM:
        positions = [
            (pad, pcbnew.VECTOR2I(pad.GetPosition().x, pad.GetPosition().y))
            for pad in native.Pads()
        ]
        native.Flip(native.GetPosition(), pcbnew.FLIP_DIRECTION_LEFT_RIGHT)
        # KiCad's flip leaves an unrotated mounting-side package at native
        # orientation 180°. A positive author rotation is counterclockwise
        # when viewing that mounting face, hence the opposite native sign.
        if pattern.board_top_view:
            for pad, position in positions:
                pad.SetPosition(position)
            native.SetOrientationDegrees(180 + component.placement.rotation_degrees)
        else:
            native.SetOrientationDegrees(180 - component.placement.rotation_degrees)
    else:
        native.SetOrientationDegrees(component.placement.rotation_degrees)
    return native


def _courtyard(
    footprint: pcbnew.FOOTPRINT,
    width_mm: float,
    height_mm: float,
    centre: Point,
    outline: BoardOutline,
) -> None:
    """Draw the reserved rectangle as four assembly-layer line segments.

    These lines communicate component clearance to board reviewers and
    assembly tools. They are not copper and do not themselves enforce spacing;
    the board-level containment check only compares this rectangle with the
    outer edge.
    """
    x, y = width_mm / 2, height_mm / 2
    corners = (Point(-x, y), Point(x, y), Point(x, -y), Point(-x, -y))
    for start, end in zip(corners, corners[1:] + corners[:1]):
        line = pcbnew.PCB_SHAPE(footprint)
        line.SetShape(pcbnew.SHAPE_T_SEGMENT)
        line.SetStart(
            native_point(
                Point(centre.x_mm + start.x_mm, centre.y_mm + start.y_mm), outline
            )
        )
        line.SetEnd(
            native_point(Point(centre.x_mm + end.x_mm, centre.y_mm + end.y_mm), outline)
        )
        line.SetLayer(pcbnew.F_CrtYd)
        line.SetWidth(pcbnew.FromMM(0.05))
        footprint.Add(line)
