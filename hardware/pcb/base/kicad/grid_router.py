"""Deterministic multilayer orthogonal router for the repeated board grid.

This is intentionally conservative: raster cells are blocked by copper plus the
full board clearance. Through-via sites are kept clear on every routed layer.
KiCad remains authoritative and checks the resulting exact geometry.
"""

from __future__ import annotations

import heapq
import math
from dataclasses import dataclass
from itertools import pairwise

from base import rules
from base.kicad.api import pcbnew

# Fine enough to escape 1.27 mm SOIC pitch while retaining conservative clearance.
GRID_MM = 0.25
TRACK_MM = rules.TRACE_WIDTH_MM
KEEP_OUT_MM = rules.CLEARANCE_MM + TRACK_MM / 2 + 0.02
LAYERS = (pcbnew.F_Cu, pcbnew.B_Cu)


def _mm(value: int) -> float:
    return pcbnew.ToMM(value)


def _cell(position: pcbnew.VECTOR2I) -> tuple[int, int]:
    return (round(_mm(position.x) / GRID_MM), round(_mm(position.y) / GRID_MM))


def _position(cell: tuple[int, int]) -> pcbnew.VECTOR2I:
    return pcbnew.VECTOR2I(
        pcbnew.FromMM(cell[0] * GRID_MM), pcbnew.FromMM(cell[1] * GRID_MM)
    )


def _blocked(
    board: pcbnew.BOARD,
    netcode: int,
    bounds: tuple[int, int, int, int],
    layers: tuple[int, ...],
    additional_via_keepouts: frozenset[tuple[int, int]],
):
    x0, y0, x1, y1 = bounds
    blocked = {layer: set() for layer in layers}
    via_forbidden = set(additional_via_keepouts)

    def mark_circle(position, radius, target_layers):
        centre_x, centre_y = _mm(position.x), _mm(position.y)
        reach = radius + KEEP_OUT_MM
        left = math.floor((centre_x - reach) / GRID_MM)
        right = math.ceil((centre_x + reach) / GRID_MM)
        top = math.floor((centre_y - reach) / GRID_MM)
        bottom = math.ceil((centre_y + reach) / GRID_MM)
        for layer in target_layers:
            cells = blocked[layer]
            for ix in range(max(x0, left), min(x1, right) + 1):
                for iy in range(max(y0, top), min(y1, bottom) + 1):
                    dx = ix * GRID_MM - centre_x
                    dy = iy * GRID_MM - centre_y
                    if dx * dx + dy * dy <= reach * reach:
                        cells.add((ix, iy))

    def mark_box(box, target_layers, extra=KEEP_OUT_MM):
        left = math.floor((_mm(box.GetLeft()) - extra) / GRID_MM)
        right = math.ceil((_mm(box.GetRight()) + extra) / GRID_MM)
        top = math.floor((_mm(box.GetTop()) - extra) / GRID_MM)
        bottom = math.ceil((_mm(box.GetBottom()) + extra) / GRID_MM)
        for layer in target_layers:
            cells = blocked[layer]
            for ix in range(max(x0, left), min(x1, right) + 1):
                for iy in range(max(y0, top), min(y1, bottom) + 1):
                    cells.add((ix, iy))

    for footprint in board.GetFootprints():
        for pad in footprint.Pads():
            if pad.GetAttribute() in {pcbnew.PAD_ATTRIB_PTH, pcbnew.PAD_ATTRIB_NPTH}:
                box = pad.GetBoundingBox()
                left = math.floor((_mm(box.GetLeft()) - 0.25) / GRID_MM)
                right = math.ceil((_mm(box.GetRight()) + 0.25) / GRID_MM)
                top = math.floor((_mm(box.GetTop()) - 0.25) / GRID_MM)
                bottom = math.ceil((_mm(box.GetBottom()) + 0.25) / GRID_MM)
                for ix in range(max(x0, left), min(x1, right) + 1):
                    for iy in range(max(y0, top), min(y1, bottom) + 1):
                        via_forbidden.add((ix, iy))
            # Same-net copper is a valid destination/tree. NPTH holes have no net
            # and must always remain clear on both outer layers.
            if pad.GetNetCode() == netcode and netcode != 0:
                continue
            copper_layers = [layer for layer in layers if pad.IsOnLayer(layer)]
            if pad.GetAttribute() == pcbnew.PAD_ATTRIB_NPTH:
                copper_layers = list(layers)
            if copper_layers:
                if pad.GetShape() == pcbnew.PAD_SHAPE_CIRCLE:
                    size = pad.GetSize()
                    mark_circle(
                        pad.GetPosition(),
                        max(_mm(size.x), _mm(size.y)) / 2,
                        copper_layers,
                    )
                else:
                    mark_box(pad.GetBoundingBox(), copper_layers)

    for track in board.GetTracks():
        if track.GetNetCode() == netcode and netcode != 0:
            continue
        box = track.GetBoundingBox()
        left = math.floor((_mm(box.GetLeft()) - KEEP_OUT_MM) / GRID_MM)
        right = math.ceil((_mm(box.GetRight()) + KEEP_OUT_MM) / GRID_MM)
        top = math.floor((_mm(box.GetTop()) - KEEP_OUT_MM) / GRID_MM)
        bottom = math.ceil((_mm(box.GetBottom()) + KEEP_OUT_MM) / GRID_MM)
        for ix in range(max(x0, left), min(x1, right) + 1):
            for iy in range(max(y0, top), min(y1, bottom) + 1):
                via_forbidden.add((ix, iy))
        if isinstance(track, pcbnew.PCB_VIA):
            mark_box(track.GetBoundingBox(), layers)
        elif track.GetLayer() in layers:
            mark_box(track.GetBoundingBox(), (track.GetLayer(),))
    return blocked, via_forbidden


@dataclass(frozen=True)
class Route:
    points: tuple[tuple[int, int, int], ...]
    layers: tuple[int, ...]


def find_route(
    board: pcbnew.BOARD,
    net,
    start: pcbnew.VECTOR2I,
    end: pcbnew.VECTOR2I,
    margin_mm: float = 150.0,
    preferred_layer_index: int | None = None,
    required_end_layer_index: int | None = None,
    allow_vias: bool = True,
    layers: tuple[int, ...] = LAYERS,
    diagonals: bool = False,
    additional_via_keepouts: frozenset[tuple[int, int]] = frozenset(),
) -> Route:
    """Find a path whose point layers are indices into ``layers``."""
    if not layers:
        raise ValueError("at least one routing layer is required")
    for label, index in (
        ("preferred start", preferred_layer_index),
        ("required end", required_end_layer_index),
    ):
        if index is not None and not 0 <= index < len(layers):
            raise ValueError(f"{label} layer index {index} is outside {layers}")

    start_cell, end_cell = _cell(start), _cell(end)
    margin = round(margin_mm / GRID_MM)
    edge = board.GetBoardEdgesBoundingBox()
    inset = rules.POUR_TO_OUTLINE_MM + TRACK_MM / 2
    board_bounds = (
        math.ceil((_mm(edge.GetLeft()) + inset) / GRID_MM),
        math.ceil((_mm(edge.GetTop()) + inset) / GRID_MM),
        math.floor((_mm(edge.GetRight()) - inset) / GRID_MM),
        math.floor((_mm(edge.GetBottom()) - inset) / GRID_MM),
    )
    bounds = (
        max(board_bounds[0], min(start_cell[0], end_cell[0]) - margin),
        max(board_bounds[1], min(start_cell[1], end_cell[1]) - margin),
        min(board_bounds[2], max(start_cell[0], end_cell[0]) + margin),
        min(board_bounds[3], max(start_cell[1], end_cell[1]) + margin),
    )
    blocked, via_forbidden = _blocked(
        board,
        net.GetNetCode(),
        bounds,
        layers,
        additional_via_keepouts,
    )
    for layer in layers:
        blocked[layer].discard(start_cell)
        blocked[layer].discard(end_cell)

    start_layers = (
        range(len(layers))
        if preferred_layer_index is None
        else (preferred_layer_index,)
    )
    starts = [(start_cell[0], start_cell[1], layer) for layer in start_layers]
    target_layers = (
        range(len(layers))
        if required_end_layer_index is None
        else (required_end_layer_index,)
    )
    targets = {(end_cell[0], end_cell[1], layer) for layer in target_layers}
    queue: list[tuple[int, int, tuple[int, int, int]]] = []
    serial = 0
    distance = {}
    previous = {}
    for node in starts:
        distance[node] = 0
        heuristic = abs(node[0] - end_cell[0]) + abs(node[1] - end_cell[1])
        heapq.heappush(queue, (heuristic, serial, node))
        serial += 1

    found = None
    while queue:
        _score, _serial, node = heapq.heappop(queue)
        cost = distance[node]
        if node in targets:
            found = node
            break
        x, y, layer_index = node
        candidates = [
            (x + 1, y, layer_index, 1),
            (x - 1, y, layer_index, 1),
            (x, y + 1, layer_index, 1),
            (x, y - 1, layer_index, 1),
        ]
        if diagonals:
            candidates.extend(
                (
                    (x + 1, y + 1, layer_index, 2),
                    (x + 1, y - 1, layer_index, 2),
                    (x - 1, y + 1, layer_index, 2),
                    (x - 1, y - 1, layer_index, 2),
                )
            )
        if allow_vias:
            candidates.extend(
                (x, y, other_layer, 16)
                for other_layer in range(len(layers))
                if other_layer != layer_index
            )
        for nx, ny, nl, step_cost in candidates:
            if not (bounds[0] <= nx <= bounds[2] and bounds[1] <= ny <= bounds[3]):
                continue
            cell = (nx, ny)
            if cell in blocked[layers[nl]]:
                continue
            if (
                diagonals
                and nx != x
                and ny != y
                and ((nx, y) in blocked[layers[nl]] or (x, ny) in blocked[layers[nl]])
            ):
                continue
            # A through via needs clearance on its source and destination. The
            # layer-independent via_forbidden map covers copper on other layers.
            if nl != layer_index and (
                cell in blocked[layers[layer_index]] or cell in via_forbidden
            ):
                continue
            candidate = (nx, ny, nl)
            new_cost = cost + step_cost
            if new_cost >= distance.get(candidate, 1 << 60):
                continue
            distance[candidate] = new_cost
            previous[candidate] = node
            heuristic = abs(nx - end_cell[0]) + abs(ny - end_cell[1])
            heapq.heappush(queue, (new_cost + heuristic, serial, candidate))
            serial += 1
    if found is None:
        raise RuntimeError(f"no route for {net.GetNetname()} in {bounds}")

    path = [found]
    while path[-1] not in starts:
        path.append(previous[path[-1]])
    path.reverse()
    # Keep endpoints, layer changes, and corners only.
    simple = [path[0]]
    for index in range(1, len(path) - 1):
        before, here, after = path[index - 1], path[index], path[index + 1]
        delta1 = (here[0] - before[0], here[1] - before[1], here[2] - before[2])
        delta2 = (after[0] - here[0], after[1] - here[1], after[2] - here[2])
        if delta1 != delta2:
            simple.append(here)
    simple.append(path[-1])
    return Route(tuple(simple), layers)


def apply_route(board: pcbnew.BOARD, net, start, end, route: Route) -> None:
    """Materialize a raster route as exact KiCad tracks and vias."""
    points = list(route.points)
    first = _position(points[0][:2])
    last = _position(points[-1][:2])

    def trace(a, b, layer_index):
        if a == b:
            return
        item = pcbnew.PCB_TRACK(board)
        item.SetStart(a)
        item.SetEnd(b)
        item.SetWidth(pcbnew.FromMM(TRACK_MM))
        item.SetLayer(route.layers[layer_index])
        item.SetNet(net)
        board.Add(item)

    trace(start, first, points[0][2])
    for left, right in pairwise(points):
        at = _position(left[:2])
        destination = _position(right[:2])
        if left[2] == right[2]:
            trace(at, destination, left[2])
        else:
            via = pcbnew.PCB_VIA(board)
            via.SetPosition(at)
            via.SetWidth(pcbnew.FromMM(rules.VIA_PAD_MM))
            via.SetDrill(pcbnew.FromMM(rules.VIA_DRILL_MM))
            via.SetNet(net)
            board.Add(via)
    trace(last, end, points[-1][2])
