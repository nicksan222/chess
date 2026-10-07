"""Materialise explicit copper route declarations as native board objects.

``Trace`` records one straight segment on an enabled copper layer;
``Via`` records one plated through-hole joining those faces. The renderer
does not invent intermediate corners, choose a path around obstacles, or
infer endpoint connectivity. Those limits keep routing declarative and make
the saved board the inspectable source for later KiCad checks.
"""

from __future__ import annotations

import pcbnew

from ...net import Net
from ..outline import BoardOutline
from ..route import CopperLayer, Trace, Via
from .units import native_point

LAYER_IDS = {
    CopperLayer.TOP: pcbnew.F_Cu,
    CopperLayer.BOTTOM: pcbnew.B_Cu,
    CopperLayer.INNER_1: pcbnew.In1_Cu,
    CopperLayer.INNER_2: pcbnew.In2_Cu,
    CopperLayer.INNER_3: pcbnew.In3_Cu,
    CopperLayer.INNER_4: pcbnew.In4_Cu,
    CopperLayer.INNER_5: pcbnew.In5_Cu,
    CopperLayer.INNER_6: pcbnew.In6_Cu,
}


def render_trace[BoardNet: Net](
    board: pcbnew.BOARD,
    route: Trace[BoardNet],
    outline: BoardOutline,
    net: pcbnew.NETINFO_ITEM,
) -> pcbnew.PCB_TRACK:
    """Add one straight native track with declared endpoints, width, and net.

    The layer enum selects the requested outer or inner copper layer. The converter does not check
    whether either endpoint touches a pad or another segment, whether the
    segment crosses an obstacle, or whether its width meets a design rule.
    """
    if net.GetNetname() != route.net.label:
        raise ValueError("native trace net must match its declared net")
    native = pcbnew.PCB_TRACK(board)
    native.SetStart(native_point(route.start, outline))
    native.SetEnd(native_point(route.end, outline))
    native.SetWidth(pcbnew.FromMM(route.width_mm))
    native.SetLayer(LAYER_IDS[route.layer])
    native.SetNet(net)
    board.Add(native)
    return native


def render_via[BoardNet: Net](
    board: pcbnew.BOARD,
    route: Via[BoardNet],
    outline: BoardOutline,
    net: pcbnew.NETINFO_ITEM,
) -> pcbnew.PCB_VIA:
    """Add a native through-via with requested copper diameter, drill, and net.

    KiCad's via spans copper layers; this declaration currently models a
    through-via and does not expose blind or buried via layer pairs. The
    renderer records the via's location and sizes but does not prove that its
    annulus, clearance, or net continuity passes manufacturing rules.
    """
    if net.GetNetname() != route.net.label:
        raise ValueError("native via net must match its declared net")
    native = pcbnew.PCB_VIA(board)
    native.SetPosition(native_point(route.center, outline))
    native.SetWidth(pcbnew.FromMM(route.diameter_mm))
    native.SetDrill(pcbnew.FromMM(route.drill_mm))
    native.SetNet(net)
    board.Add(native)
    return native
