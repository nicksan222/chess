"""Turn one declarative land pattern entry into a native KiCad pad.

The harness records a pad's number, shape, dimensions, kind, drill, and
logical pin without importing KiCad. The renderer materialises that record as
a ``pcbnew.PAD`` owned by a native footprint, including its copper-layer set
and optional ``NETINFO_ITEM``. A pad is physical copper geometry; it is not
evidence that a real component, solder joint, or route will fit it.
"""

from __future__ import annotations

from enum import StrEnum

import pcbnew

from ...connections import NetConnection, PinConnection
from ..outline import BoardOutline
from ..pad import Pad, PadKind, PadShape
from ..point import Point
from .units import native_point


def render_pad[Pin: StrEnum](
    footprint: pcbnew.FOOTPRINT,
    pad: Pad[Pin],
    connection: PinConnection,
    outline: BoardOutline,
    net: pcbnew.NETINFO_ITEM | None,
    centre: Point,
) -> pcbnew.PAD:
    """Create one native copper land/drill and assign its intended network.

    The component centre and package-local pad offset determine its board
    position in the centred harness coordinate system. Dimensions convert
    from millimetres to KiCad's internal units.
    Surface pads receive front/back surface-mount layers; through-hole pads
    receive plated-hole layers and a drill size. A ``NoConnect`` intentionally
    has no native net. A connected pad must receive the matching native net
    from the board renderer. This creates geometry and metadata; it does not
    prove the pad fits the physical component lead, clears neighbouring
    copper, or is connected by a routed track.
    """
    if isinstance(connection, NetConnection) != (net is not None) or (
        isinstance(connection, NetConnection)
        and net is not None
        and net.GetNetname() != connection.net.label
    ):
        raise ValueError("native pad net must match its logical connection")
    native = pcbnew.PAD(footprint)
    native.SetNumber(pad.physical_number)
    native.SetPosition(
        native_point(
            Point(centre.x_mm + pad.center.x_mm, centre.y_mm + pad.center.y_mm), outline
        )
    )
    native.SetSize(
        pcbnew.VECTOR2I(pcbnew.FromMM(pad.width_mm), pcbnew.FromMM(pad.height_mm))
    )
    native.SetShape(
        {
            PadShape.RECTANGLE: pcbnew.PAD_SHAPE_RECT,
            PadShape.CIRCLE: pcbnew.PAD_SHAPE_CIRCLE,
            PadShape.OVAL: pcbnew.PAD_SHAPE_OVAL,
        }[pad.shape]
    )
    if pad.kind is PadKind.SURFACE:
        native.SetAttribute(pcbnew.PAD_ATTRIB_SMD)
        native.SetLayerSet(native.SMDMask())
    else:
        native.SetAttribute(pcbnew.PAD_ATTRIB_PTH)
        native.SetDrillSize(
            pcbnew.VECTOR2I(pcbnew.FromMM(pad.drill_mm), pcbnew.FromMM(pad.drill_mm))
        )
        native.SetLayerSet(native.PTHMask())
    if net is not None:
        native.SetNet(net)
    footprint.Add(native)
    return native
