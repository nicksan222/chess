"""Deterministic multilayer grid search and copper obstacle rasterization.

Role: the pathfinding engine behind the routing policies in `policies.py`. Given a
board, a net and two endpoints it (1) rasterizes all copper of *other* nets onto a
0.25 mm grid as blocked cells, (2) runs an A* search over (x, y, layer) cells, and
(3) `apply_route` turns the resulting path into exact KiCad tracks and vias.

Why a custom grid router: output must be reproducible byte for byte (ties are broken
by insertion order, never by hashing), and routing happens inside the same Python
build as placement, so there is no external router in the loop for these nets.
Coordinates here are KiCad's (absolute, Y down); grid cells are integers in units of
`GRID_MM`.
"""

from __future__ import annotations

import heapq
import math
from dataclasses import dataclass
from itertools import pairwise
from typing import TypedDict

import pcbnew

from . import copper as native
from .settings import RoutingSettings

# Routing grid pitch. Endpoints are snapped to it; `apply_route` re-attaches the
# exact (off-grid) pad positions with short stubs.
GRID_MM = 0.25
DEFAULT_SETTINGS = RoutingSettings()


def mm(value: int) -> float:
    return pcbnew.ToMM(value)


def grid_cell(position: pcbnew.VECTOR2I) -> tuple[int, int]:
    return (round(mm(position.x) / GRID_MM), round(mm(position.y) / GRID_MM))


def position(cell: tuple[int, int]) -> pcbnew.VECTOR2I:
    """Inverse of `grid_cell`: the KiCad position of a cell's centre."""
    return pcbnew.VECTOR2I(
        pcbnew.FromMM(cell[0] * GRID_MM), pcbnew.FromMM(cell[1] * GRID_MM)
    )


def blocked_cells(
    board: pcbnew.BOARD,
    netcode: int,
    bounds: tuple[int, int, int, int],
    layers: tuple[int, ...],
    additional_via_keepouts: frozenset[tuple[int, int]],
    settings: RoutingSettings = DEFAULT_SETTINGS,
) -> tuple[dict[int, set[tuple[int, int]]], set[tuple[int, int]]]:
    """Rasterize foreign copper separately for tracks and full-stack vias.

    Returns (blocked, via_forbidden). `blocked[layer]` holds cells where a track
    centre may not go on that layer. `via_forbidden` is layer-independent: a through
    via pierces every layer, so it must also avoid copper and drills on layers the
    route does not use. `bounds` limits work to the search window
    (x0, y0, x1, y1 in cells); `additional_via_keepouts` adds caller-owned via bans.
    Copper on `netcode` is skipped (it is a legal destination); net 0 never matches.
    """
    x0, y0, x1, y1 = bounds
    blocked: dict[int, set[tuple[int, int]]] = {layer: set() for layer in layers}
    via_forbidden = set(additional_via_keepouts)

    # Mark every cell within `radius + extra` of a circle's centre.
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

    # Mark every cell inside a bounding box grown by `extra` (conservative for
    # non-circular pads and for tracks, whose boxes over-cover diagonals).
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

    # Pads first: they are the fixed obstacles.
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
                (track_targets, settings.track_keepout_mm),
                (via_targets, settings.via_keepout_mm),
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

    # Then copper already routed for other nets, including earlier routing stages.
    def mark_segment(
        track: pcbnew.PCB_TRACK,
        targets: tuple[set[tuple[int, int]], ...],
        extra: float,
    ) -> None:
        """Cells within reach of the segment itself, not of its bounding box.

        A diagonal track's bounding box can span tens of millimetres and would wall
        off whole regions of a layer that the copper never occupies.
        """
        start, end = track.GetStart(), track.GetEnd()
        ax, ay, bx, by = mm(start.x), mm(start.y), mm(end.x), mm(end.y)
        reach = mm(track.GetWidth()) / 2 + extra
        dx, dy = bx - ax, by - ay
        length = dx * dx + dy * dy
        left = math.floor((min(ax, bx) - reach) / GRID_MM)
        right = math.ceil((max(ax, bx) + reach) / GRID_MM)
        top = math.floor((min(ay, by) - reach) / GRID_MM)
        bottom = math.ceil((max(ay, by) + reach) / GRID_MM)
        for ix in range(max(x0, left), min(x1, right) + 1):
            for iy in range(max(y0, top), min(y1, bottom) + 1):
                px, py = ix * GRID_MM, iy * GRID_MM
                t = 0.0 if length == 0 else ((px - ax) * dx + (py - ay) * dy) / length
                t = min(max(t, 0.0), 1.0)
                if math.hypot(ax + t * dx - px, ay + t * dy - py) <= reach:
                    for cells in targets:
                        cells.add((ix, iy))

    for track in board.GetTracks():
        if track.GetNetCode() == netcode and netcode != 0:
            continue
        if isinstance(track, pcbnew.PCB_VIA):
            box = track.GetBoundingBox()
            mark_box(box, (via_forbidden,), settings.via_keepout_mm)
            mark_box(box, tuple(blocked.values()), settings.track_keepout_mm)
            continue
        mark_segment(track, (via_forbidden,), settings.via_keepout_mm)
        if track.GetLayer() in layers:
            mark_segment(track, (blocked[track.GetLayer()],), settings.track_keepout_mm)
    return blocked, via_forbidden


# Default routing layers: the two outer copper layers. Policies pass internal
# signal layers explicitly when they route inside the stack.
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


@dataclass(frozen=True, slots=True)
class GridNode:
    """One routing-grid cell on a specific index into a route's layers.

    `layer_index` indexes the `layers` tuple of the search, not a KiCad layer id.
    """

    x: int
    y: int
    layer_index: int

    @classmethod
    def from_cell(cls, cell: tuple[int, int], layer_index: int) -> GridNode:
        return cls(cell[0], cell[1], layer_index)

    @property
    def cell(self) -> tuple[int, int]:
        return (self.x, self.y)

    def direction_from(self, other: GridNode) -> tuple[int, int, int]:
        """Step vector from `other` to this node; used to detect corners."""
        return (
            self.x - other.x,
            self.y - other.y,
            self.layer_index - other.layer_index,
        )


@dataclass(frozen=True, slots=True)
class Route:
    """Simplified raster points with layer indices, not native KiCad layer IDs.

    `points` keeps only endpoints, corners and layer changes; `layers` is the tuple
    the indices refer to, so `apply_route` can map them back to KiCad layers.
    """

    points: tuple[GridNode, ...]
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
    settings: RoutingSettings = DEFAULT_SETTINGS,
) -> Route:
    """Find a path whose point layers are indices into ``layers``.

    ``routing_bounds_mm`` is an absolute KiCad-coordinate rectangle ordered
    (left, top, right, bottom), with Y increasing downward. It limits track
    centre lines (including exact endpoint stubs), not the full copper width.
    Board-edge restrictions additionally reserve clearance for tracks and vias.

    Other parameters: `margin_mm` pads the search window around the endpoints'
    bounding box (bigger is slower but finds detours). `preferred_layer_index`
    fixes the layer the route starts on and `required_end_layer_index` the layer it
    must finish on (None = any). `allow_vias` permits layer changes; `diagonals`
    permits 45-degree steps. `additional_via_keepouts` are extra cells where vias
    are banned. Raises RuntimeError when no path exists, and ValueError when the
    endpoints themselves are illegal; callers rely on the former to try fallbacks.
    """
    if not layers:
        raise ValueError("at least one routing layer is required")
    for label, index in (
        ("preferred start", preferred_layer_index),
        ("required end", required_end_layer_index),
    ):
        if index is not None and not 0 <= index < len(layers):
            raise ValueError(f"{label} layer index {index} is outside {layers}")

    # --- Bounds: stay inside the board edge by the pour margin plus half a track.
    # Check exact endpoints before snapping: a legal cell can hide an illegal stub.
    start_cell, end_cell = grid_cell(start), grid_cell(end)
    margin = round(margin_mm / GRID_MM)
    edge = board.GetBoardEdgesBoundingBox()
    inset = settings.edge_clearance_mm + settings.track_width_mm / 2
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
    # Convert the allowed rectangle to cells, rounding inward so a snapped cell is
    # never outside the exact bounds.
    board_bounds = (
        math.ceil(left / GRID_MM),
        math.ceil(top / GRID_MM),
        math.floor(right / GRID_MM),
        math.floor(bottom / GRID_MM),
    )
    # Vias are bigger than tracks, so they need a larger edge inset.
    via_inset = settings.edge_clearance_mm + settings.via_diameter_mm / 2
    via_bounds = (
        math.ceil((mm(edge.GetLeft()) + via_inset) / GRID_MM),
        math.ceil((mm(edge.GetTop()) + via_inset) / GRID_MM),
        math.floor((mm(edge.GetRight()) - via_inset) / GRID_MM),
        math.floor((mm(edge.GetBottom()) - via_inset) / GRID_MM),
    )
    # Search window: the endpoints' box grown by `margin`, clipped to the board.
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
        settings,
    )
    # The endpoints sit on pads of this net, so they must be reachable even if a
    # neighbour's keepout touches their cell.
    for layer in layers:
        blocked[layer].discard(start_cell)
        blocked[layer].discard(end_cell)

    # --- A* search. Start on any layer (or the preferred one) and finish on any
    # layer (or the required one).
    start_layers = (
        range(len(layers))
        if preferred_layer_index is None
        else (preferred_layer_index,)
    )
    starts = [GridNode.from_cell(start_cell, layer) for layer in start_layers]
    target_layers = (
        range(len(layers))
        if required_end_layer_index is None
        else (required_end_layer_index,)
    )
    targets = {GridNode.from_cell(end_cell, layer) for layer in target_layers}
    # Serial numbers preserve neighbour order when A* scores tie. Via changes cost
    # more than planar steps so the search prefers staying on the current layer.
    queue: list[tuple[int, int, GridNode]] = []
    serial = 0
    # Best known cost to each node, and the predecessor for path reconstruction.
    distance: dict[GridNode, int] = {}
    previous: dict[GridNode, GridNode] = {}
    for node in starts:
        distance[node] = 0
        heuristic = abs(node.x - end_cell[0]) + abs(node.y - end_cell[1])
        heapq.heappush(queue, (heuristic, serial, node))
        serial += 1

    found = None
    while queue:
        _score, _serial, node = heapq.heappop(queue)
        cost = distance[node]
        if node in targets:
            found = node
            break
        x, y, layer_index = node.x, node.y, node.layer_index
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
        # A via costs 16 steps: layer changes cost copper and manufacturability, so
        # the search only makes one when it saves a lot of detour.
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
            # Forbid cutting a corner between two blocked cells on a diagonal step.
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
            candidate = GridNode(nx, ny, nl)
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

    # Walk predecessors back to a start node, then reverse.
    path = [found]
    while path[-1] not in starts:
        path.append(previous[path[-1]])
    path.reverse()
    # Keep endpoints, layer changes, and corners only.
    simple = [path[0]]
    for index in range(1, len(path) - 1):
        before, here, after = path[index - 1], path[index], path[index + 1]
        if here.direction_from(before) != after.direction_from(here):
            simple.append(here)
    simple.append(path[-1])
    return Route(tuple(simple), layers)


def apply_route(
    board: pcbnew.BOARD,
    net: pcbnew.NETINFO_ITEM,
    start: pcbnew.VECTOR2I,
    end: pcbnew.VECTOR2I,
    route: Route,
    settings: RoutingSettings = DEFAULT_SETTINGS,
) -> None:
    """Materialize a raster route as exact KiCad tracks and vias.

    `start`/`end` are the true (possibly off-grid) pad positions; short stubs join
    them to the first/last grid cell. Each layer change becomes a via at that cell.
    """
    points = list(route.points)
    first = position(points[0].cell)
    last = position(points[-1].cell)

    def trace(a: pcbnew.VECTOR2I, b: pcbnew.VECTOR2I, layer_index: int) -> None:
        if a == b:
            return
        native.add_trace(
            board, net, a, b, route.layers[layer_index], settings.track_width_mm
        )

    trace(start, first, points[0].layer_index)
    for left, right in pairwise(points):
        at = position(left.cell)
        destination = position(right.cell)
        if left.layer_index == right.layer_index:
            trace(at, destination, left.layer_index)
        else:
            native.add_via(
                board, net, at, settings.via_diameter_mm, settings.via_drill_mm
            )
    trace(last, end, points[-1].layer_index)
