"""Routing primitives shared by focused product routers."""

from __future__ import annotations

import math
from collections import defaultdict

from base.component import ComponentReference
from base.kicad import board as kicad
from base.kicad import grid_router
from base.kicad.api import pcbnew
from board.wiring.nets import ButtonNet, Net

EXPANDER_REFERENCES = frozenset({"U1", "U2", "U3", "U4"})
DENSE_SOIC_REFERENCES = EXPANDER_REFERENCES | {"U5"}
INTERNAL_SIGNAL_LAYERS = (pcbnew.In4_Cu, pcbnew.In5_Cu, pcbnew.In6_Cu)
SENSOR_ROUTING_LAYERS = (pcbnew.F_Cu, pcbnew.B_Cu, *INTERNAL_SIGNAL_LAYERS)
CONTROL_SIGNAL_NETS = frozenset(
    {Net.SPI_CLOCK, Net.SPI_DATA, Net.LED_CLOCK, Net.LED_DATA}
)
OPTIONAL_ESCAPE_VIA_NETS = CONTROL_SIGNAL_NETS


def footprint(board: pcbnew.BOARD, reference: str) -> pcbnew.FOOTPRINT:
    """Resolve exactly one native footprint by its semantic reference."""
    matches = [
        item for item in board.GetFootprints() if item.GetReference() == reference
    ]
    if len(matches) != 1:
        raise RuntimeError(f"expected one {reference} footprint; found {len(matches)}")
    return matches[0]


def _host_header_via_keepouts(board) -> frozenset[tuple[int, int]]:
    """Protect this board's narrow Pi button-signal launch channels."""
    header = footprint(board, ComponentReference.HOST_GPIO_HEADER)
    header_y = pcbnew.ToMM(header.GetPosition().y)
    forbidden = set()
    for pad in header.Pads():
        if pad.GetNetname() not in ButtonNet:
            continue
        centre = pad.GetPosition()
        cx, cy = pcbnew.ToMM(centre.x), pcbnew.ToMM(centre.y)
        direction = 1 if cy > header_y else -1
        left = math.floor((cx - 1.2) / grid_router.GRID_MM)
        right = math.ceil((cx + 1.2) / grid_router.GRID_MM)
        near = math.floor(cy / grid_router.GRID_MM)
        far = math.ceil((cy + direction * 6.0) / grid_router.GRID_MM)
        forbidden.update(
            (x, y)
            for x in range(left, right + 1)
            for y in range(min(near, far), max(near, far) + 1)
        )
    return frozenset(forbidden)


def find_route(board, net, start, end, **options):
    """Route with chess-board-specific keep-outs applied to the base router."""
    return grid_router.find_route(
        board,
        net,
        start,
        end,
        additional_via_keepouts=_host_header_via_keepouts(board),
        **options,
    )


def signal_escape(board, net, pad, *, add_via=False):
    """Fan an SMD signal pad straight away from its package before routing.

    The grid router treats adjacent pads as obstacles. SOIC and SOT-23 pitches
    therefore need a short exact-geometry escape before entering its routing grid.
    """
    if pad.GetAttribute() != pcbnew.PAD_ATTRIB_SMD:
        return pad.GetPosition()
    at = pad.GetPosition()
    footprint = pad.GetParentFootprint()
    centre = footprint.GetPosition()
    dx, dy = at.x - centre.x, at.y - centre.y
    escape_mm = 3.0 if footprint.GetReference().startswith("HS") else 2.0
    # Stagger dense SOIC breakouts so adjacent 1.27 mm rows do not form a wall
    # of through-vias around the package.
    is_soic = footprint.GetReference() in DENSE_SOIC_REFERENCES
    if is_soic:
        escape_mm += (int(pad.GetNumber()) - 1) % 4
    distance = pcbnew.FromMM(escape_mm)
    if is_soic or abs(dx) >= abs(dy):
        escaped = pcbnew.VECTOR2I(at.x + (distance if dx >= 0 else -distance), at.y)
    else:
        escaped = pcbnew.VECTOR2I(at.x, at.y + (distance if dy >= 0 else -distance))
    kicad.add_trace(board, net, at, escaped)
    if add_via:
        kicad.add_via(board, net, escaped)
    return escaped


def nearest_tree_edges(nodes, route_points):
    """Yield deterministic nearest-neighbour edges connecting every node."""
    connected = {0}
    remaining = set(range(1, len(nodes)))
    while remaining:
        left, right = min(
            ((left, right) for left in connected for right in remaining),
            key=lambda pair: (
                abs(route_points[nodes[pair[0]]].x - route_points[nodes[pair[1]]].x)
                + abs(route_points[nodes[pair[0]]].y - route_points[nodes[pair[1]]].y),
                pair,
            ),
        )
        yield nodes[left], nodes[right]
        connected.add(right)
        remaining.remove(right)


def prune_unused_signal_vias(board: pcbnew.BOARD) -> None:
    """Remove optional escape vias from routes that stayed on one layer."""
    vias = []
    layers_at_endpoint = defaultdict(set)
    for item in board.GetTracks():
        if isinstance(item, pcbnew.PCB_VIA):
            vias.append(item)
            continue
        for endpoint in (item.GetStart(), item.GetEnd()):
            key = (item.GetNetCode(), endpoint.x, endpoint.y)
            layers_at_endpoint[key].add(item.GetLayer())

    for via in vias:
        name = via.GetNetname()
        if not name.startswith("SQ_") and name not in OPTIONAL_ESCAPE_VIA_NETS:
            continue
        at = via.GetPosition()
        key = (via.GetNetCode(), at.x, at.y)
        if len(layers_at_endpoint[key]) < 2:
            board.Remove(via)
