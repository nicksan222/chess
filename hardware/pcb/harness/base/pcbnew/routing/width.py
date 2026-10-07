"""Clip narrow package copper to its declared courtyard margin."""

from enum import StrEnum

import pcbnew

from ...component import BoardComponent
from ...geometry import Side
from . import copper


def _courtyard(
    board: pcbnew.BOARD, reference: str, layer: int
) -> tuple[int, int, int, int]:
    """The component's F.CrtYd rectangle (left, top, right, bottom) in board units."""
    module = board.FindFootprintByReference(reference)
    if module is None:
        raise ValueError("the package clearance needs its footprint")
    points = [
        p
        for shape in module.GraphicalItems()
        if shape.GetLayer() == layer
        for p in (shape.GetStart(), shape.GetEnd())
    ]
    xs, ys = [p.x for p in points], [p.y for p in points]
    return min(xs), min(ys), max(xs), max(ys)


def _clip(
    start: pcbnew.VECTOR2I, end: pcbnew.VECTOR2I, box: tuple[int, int, int, int]
) -> tuple[float, float] | None:
    """Liang-Barsky: the parameter span of start->end inside `box`, if any."""
    t0, t1 = 0.0, 1.0
    dx, dy = end.x - start.x, end.y - start.y
    left, top, right, bottom = box
    for p, q in (
        (-dx, start.x - left),
        (dx, right - start.x),
        (-dy, start.y - top),
        (dy, bottom - start.y),
    ):
        if p == 0:
            if q < 0:
                return None
            continue
        t = q / p
        if p < 0:
            t0 = max(t0, t)
        else:
            t1 = min(t1, t)
    return (t0, t1) if t0 <= t1 else None


def _along(start: pcbnew.VECTOR2I, end: pcbnew.VECTOR2I, t: float) -> pcbnew.VECTOR2I:
    """The point at fraction `t` (0-1) along the segment start->end."""
    return pcbnew.VECTOR2I(
        round(start.x + t * (end.x - start.x)), round(start.y + t * (end.y - start.y))
    )


def split_package_escapes(
    board: pcbnew.BOARD, component: BoardComponent[StrEnum], track_width_mm: float
) -> None:
    """Limit a package's narrow copper exception to its courtyard escape margin."""
    rule = component.definition.routing.clearance
    if rule is None:
        return
    bottom_side = component.placement.side is Side.BOTTOM
    layer = pcbnew.B_Cu if bottom_side else pcbnew.F_Cu
    left, top, right, bottom = _courtyard(
        board, component.reference, pcbnew.B_CrtYd if bottom_side else pcbnew.F_CrtYd
    )
    margin = pcbnew.FromMM(rule.escape_margin_mm)
    escape = (left - margin, top - margin, right + margin, bottom + margin)
    for track in list(board.GetTracks()):
        if isinstance(track, pcbnew.PCB_VIA) or track.GetLayer() != layer:
            continue
        start, end = track.GetStart(), track.GetEnd()
        half = track.GetWidth() // 2
        touching = (left - half, top - half, right + half, bottom + half)
        inside = _clip(start, end, escape)
        if _clip(start, end, touching) is None or inside is None:
            continue
        t0, t1 = inside
        if t0 <= 0.0 and t1 >= 1.0:
            continue

        net, width = track.GetNet(), pcbnew.ToMM(track.GetWidth())
        outer = max(width, track_width_mm)
        board.Remove(track)
        cut0, cut1 = _along(start, end, t0), _along(start, end, t1)
        copper.add_trace(board, net, cut0, cut1, layer, width)
        if t0 > 0.0:
            copper.add_trace(board, net, start, cut0, layer, outer)
        if t1 < 1.0:
            copper.add_trace(board, net, cut1, end, layer, outer)
