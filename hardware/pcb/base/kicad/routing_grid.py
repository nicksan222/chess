"""Grid coordinates and conservative copper keepouts for the native router.

Track obstacles are layer-specific; through-via obstacles include every copper
layer, even layers not selected for routing. KiCad DRC checks exact geometry
rather than this deliberately conservative raster approximation.
"""

from __future__ import annotations

import math

from base import rules
from base.kicad.api import pcbnew

# Fine enough to escape 1.27 mm SOIC pitch while retaining conservative clearance.
GRID_MM = 0.25
TRACK_MM = rules.TRACE_WIDTH_MM
TRACK_KEEP_OUT_MM = rules.CLEARANCE_MM + TRACK_MM / 2 + 0.02
VIA_KEEP_OUT_MM = rules.CLEARANCE_MM + rules.VIA_PAD_MM / 2 + 0.02


def mm(value: int) -> float:
    return pcbnew.ToMM(value)


def cell(position: pcbnew.VECTOR2I) -> tuple[int, int]:
    return (round(mm(position.x) / GRID_MM), round(mm(position.y) / GRID_MM))


def position(cell: tuple[int, int]) -> pcbnew.VECTOR2I:
    return pcbnew.VECTOR2I(
        pcbnew.FromMM(cell[0] * GRID_MM), pcbnew.FromMM(cell[1] * GRID_MM)
    )


def blocked_cells(
    board: pcbnew.BOARD,
    netcode: int,
    bounds: tuple[int, int, int, int],
    layers: tuple[int, ...],
    additional_via_keepouts: frozenset[tuple[int, int]],
) -> tuple[dict[int, set[tuple[int, int]]], set[tuple[int, int]]]:
    """Rasterize foreign copper separately for tracks and full-stack vias."""
    x0, y0, x1, y1 = bounds
    blocked: dict[int, set[tuple[int, int]]] = {layer: set() for layer in layers}
    via_forbidden = set(additional_via_keepouts)

    def mark_circle(
        position: pcbnew.VECTOR2I,
        radius: float,
        targets: tuple[set[tuple[int, int]], ...],
        extra: float,
    ) -> None:
        centre_x, centre_y = mm(position.x), mm(position.y)
        reach = radius + extra
        left = math.floor((centre_x - reach) / GRID_MM)
        right = math.ceil((centre_x + reach) / GRID_MM)
        top = math.floor((centre_y - reach) / GRID_MM)
        bottom = math.ceil((centre_y + reach) / GRID_MM)
        for ix in range(max(x0, left), min(x1, right) + 1):
            for iy in range(max(y0, top), min(y1, bottom) + 1):
                dx = ix * GRID_MM - centre_x
                dy = iy * GRID_MM - centre_y
                if dx * dx + dy * dy <= reach * reach:
                    for cells in targets:
                        cells.add((ix, iy))

    def mark_box(
        box: pcbnew.BOX2I, targets: tuple[set[tuple[int, int]], ...], extra: float
    ) -> None:
        left = math.floor((mm(box.GetLeft()) - extra) / GRID_MM)
        right = math.ceil((mm(box.GetRight()) + extra) / GRID_MM)
        top = math.floor((mm(box.GetTop()) - extra) / GRID_MM)
        bottom = math.ceil((mm(box.GetBottom()) + extra) / GRID_MM)
        for ix in range(max(x0, left), min(x1, right) + 1):
            for iy in range(max(y0, top), min(y1, bottom) + 1):
                for cells in targets:
                    cells.add((ix, iy))

    for footprint in board.GetFootprints():
        for pad in footprint.Pads():
            is_hole = pad.GetAttribute() in {
                pcbnew.PAD_ATTRIB_PTH,
                pcbnew.PAD_ATTRIB_NPTH,
            }
            if is_hole:
                # Retain the separate drill keepout even for same-net pads.
                mark_box(pad.GetBoundingBox(), (via_forbidden,), 0.25)
            # Same-net copper is a valid destination/tree. NPTH holes have no net
            # and must always remain clear on every routing layer.
            if pad.GetNetCode() == netcode and netcode != 0:
                continue
            copper_layers = [layer for layer in layers if pad.IsOnLayer(layer)]
            if pad.GetAttribute() == pcbnew.PAD_ATTRIB_NPTH:
                copper_layers = list(layers)
            track_targets = tuple(blocked[layer] for layer in copper_layers)
            # Through vias cross outer pads even when routing only on inner layers.
            via_targets = (
                (via_forbidden,) if is_hole or pad.GetLayerSet().CuStack() else ()
            )
            for targets, extra in (
                (track_targets, TRACK_KEEP_OUT_MM),
                (via_targets, VIA_KEEP_OUT_MM),
            ):
                if not targets:
                    continue
                if pad.GetShape() == pcbnew.PAD_SHAPE_CIRCLE:
                    size = pad.GetSize()
                    mark_circle(
                        pad.GetPosition(),
                        max(mm(size.x), mm(size.y)) / 2,
                        targets,
                        extra,
                    )
                else:
                    mark_box(pad.GetBoundingBox(), targets, extra)

    for track in board.GetTracks():
        if track.GetNetCode() == netcode and netcode != 0:
            continue
        box = track.GetBoundingBox()
        mark_box(box, (via_forbidden,), VIA_KEEP_OUT_MM)
        if isinstance(track, pcbnew.PCB_VIA):
            mark_box(box, tuple(blocked.values()), TRACK_KEEP_OUT_MM)
        elif track.GetLayer() in layers:
            mark_box(box, (blocked[track.GetLayer()],), TRACK_KEEP_OUT_MM)
    return blocked, via_forbidden
