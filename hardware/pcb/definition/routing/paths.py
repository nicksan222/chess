"""Deterministic multilayer grid search and copper obstacle rasterization."""

from __future__ import annotations

import heapq
import math
from dataclasses import dataclass
from itertools import pairwise
from typing import TypedDict

import pcbnew

from pcb.definition import rules

GRID_MM = 0.25

TRACK_MM = rules.TRACE_WIDTH_MM

TRACK_KEEP_OUT_MM = rules.CLEARANCE_MM + TRACK_MM / 2 + 0.02

VIA_KEEP_OUT_MM = rules.CLEARANCE_MM + rules.VIA_PAD_MM / 2 + 0.02


def mm(value: int) -> float:
    return pcbnew.ToMM(value)


def grid_cell(position: pcbnew.VECTOR2I) -> tuple[int, int]:
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


LAYERS = (pcbnew.F_Cu, pcbnew.B_Cu)


class RoutingOptions(TypedDict, total=False):
    """Typed search-policy keywords shared by native subsystem routing stages.

    Via keepouts are deliberately absent: the board-level routing boundary owns
    those, rather than allowing individual stages to bypass header protection.
    """

    margin_mm: float
    preferred_layer_index: int | None
    required_end_layer_index: int | None
    allow_vias: bool
    layers: tuple[int, ...]
    diagonals: bool
    routing_bounds_mm: tuple[float, float, float, float] | None


@dataclass(frozen=True)
class Route:
    """Simplified raster points with layer indices, not native KiCad layer IDs."""

    points: tuple[tuple[int, int, int], ...]
    layers: tuple[int, ...]


def find_route(
    board: pcbnew.BOARD,
    net: pcbnew.NETINFO_ITEM,
    start: pcbnew.VECTOR2I,
    end: pcbnew.VECTOR2I,
    margin_mm: float = 150.0,
    preferred_layer_index: int | None = None,
    required_end_layer_index: int | None = None,
    allow_vias: bool = True,
    layers: tuple[int, ...] = LAYERS,
    diagonals: bool = False,
    additional_via_keepouts: frozenset[tuple[int, int]] = frozenset(),
    routing_bounds_mm: tuple[float, float, float, float] | None = None,
) -> Route:
    """Find a path whose point layers are indices into ``layers``.

    ``routing_bounds_mm`` is an absolute KiCad-coordinate rectangle ordered
    (left, top, right, bottom), with Y increasing downward. It limits track
    centre lines (including exact endpoint stubs), not the full copper width.
    Board-edge restrictions additionally reserve clearance for tracks and vias.
    """
    if not layers:
        raise ValueError("at least one routing layer is required")
    for label, index in (
        ("preferred start", preferred_layer_index),
        ("required end", required_end_layer_index),
    ):
        if index is not None and not 0 <= index < len(layers):
            raise ValueError(f"{label} layer index {index} is outside {layers}")

    # Check exact endpoints before snapping: a legal cell can hide an illegal stub.
    start_cell, end_cell = grid_cell(start), grid_cell(end)
    margin = round(margin_mm / GRID_MM)
    edge = board.GetBoardEdgesBoundingBox()
    inset = rules.POUR_TO_OUTLINE_MM + TRACK_MM / 2
    exact_bounds = (
        mm(edge.GetLeft()) + inset,
        mm(edge.GetTop()) + inset,
        mm(edge.GetRight()) - inset,
        mm(edge.GetBottom()) - inset,
    )
    if routing_bounds_mm is not None:
        left, top, right, bottom = routing_bounds_mm
        exact_bounds = (
            max(exact_bounds[0], left),
            max(exact_bounds[1], top),
            min(exact_bounds[2], right),
            min(exact_bounds[3], bottom),
        )
    left, top, right, bottom = exact_bounds
    if left > right or top > bottom:
        raise ValueError(f"empty routing bounds: {exact_bounds}")
    for label, endpoint in (("start", start), ("end", end)):
        if not (left <= mm(endpoint.x) <= right and top <= mm(endpoint.y) <= bottom):
            raise ValueError(
                f"{label} endpoint is outside routing bounds {exact_bounds}"
            )
    board_bounds = (
        math.ceil(left / GRID_MM),
        math.ceil(top / GRID_MM),
        math.floor(right / GRID_MM),
        math.floor(bottom / GRID_MM),
    )
    via_inset = rules.POUR_TO_OUTLINE_MM + rules.VIA_PAD_MM / 2
    via_bounds = (
        math.ceil((mm(edge.GetLeft()) + via_inset) / GRID_MM),
        math.ceil((mm(edge.GetTop()) + via_inset) / GRID_MM),
        math.floor((mm(edge.GetRight()) - via_inset) / GRID_MM),
        math.floor((mm(edge.GetBottom()) - via_inset) / GRID_MM),
    )
    bounds = (
        max(board_bounds[0], min(start_cell[0], end_cell[0]) - margin),
        max(board_bounds[1], min(start_cell[1], end_cell[1]) - margin),
        min(board_bounds[2], max(start_cell[0], end_cell[0]) + margin),
        min(board_bounds[3], max(start_cell[1], end_cell[1]) + margin),
    )
    if bounds[0] > bounds[2] or bounds[1] > bounds[3]:
        raise ValueError(f"empty routing cell bounds: {bounds}")
    for label, cell in (("start", start_cell), ("end", end_cell)):
        if not (
            bounds[0] <= cell[0] <= bounds[2] and bounds[1] <= cell[1] <= bounds[3]
        ):
            raise ValueError(
                f"snapped {label} endpoint is outside routing cell bounds {bounds}"
            )
    blocked, via_forbidden = blocked_cells(
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
    # Serial numbers preserve neighbour order when A* scores tie. Via changes cost
    # more than planar steps so the search prefers staying on the current layer.
    queue: list[tuple[int, int, tuple[int, int, int]]] = []
    serial = 0
    distance: dict[tuple[int, int, int], int] = {}
    previous: dict[tuple[int, int, int], tuple[int, int, int]] = {}
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
                cell in blocked[layers[layer_index]]
                or cell in via_forbidden
                or not (
                    via_bounds[0] <= nx <= via_bounds[2]
                    and via_bounds[1] <= ny <= via_bounds[3]
                )
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


def apply_route(
    board: pcbnew.BOARD,
    net: pcbnew.NETINFO_ITEM,
    start: pcbnew.VECTOR2I,
    end: pcbnew.VECTOR2I,
    route: Route,
) -> None:
    """Materialize a raster route as exact KiCad tracks and vias."""
    points = list(route.points)
    first = position(points[0][:2])
    last = position(points[-1][:2])

    def trace(a: pcbnew.VECTOR2I, b: pcbnew.VECTOR2I, layer_index: int) -> None:
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
        at = position(left[:2])
        destination = position(right[:2])
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
