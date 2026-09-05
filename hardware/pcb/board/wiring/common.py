"""Routing primitives shared by focused product routers."""

from __future__ import annotations

import math
from collections import defaultdict
from collections.abc import Iterator, Mapping, Sequence
from typing import Unpack

from base.component import ComponentReference
from base.connectivity import EndpointKey
from base.kicad import board as kicad
from base.kicad import grid_router
from base.kicad.api import pcbnew
from board.wiring.nets import ButtonNet, Net
from components import catalog
from components.raspberry_pi_header import RaspberryPiHeader
from components.tca9554 import Tca9554

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


def _host_header_via_keepouts(board: pcbnew.BOARD) -> frozenset[tuple[int, int]]:
    """Protect this board's narrow Pi button-signal launch channels."""
    header = footprint(board, ComponentReference.HOST_GPIO_HEADER)
    header_y = pcbnew.ToMM(header.GetPosition().y)
    forbidden: set[tuple[int, int]] = set()
    for pad in header.Pads():
        if pad.GetNetname() not in ButtonNet:
            continue
        centre = pad.GetPosition()
        cx, cy = pcbnew.ToMM(centre.x), pcbnew.ToMM(centre.y)
        direction = 1 if cy > header_y else -1
        half_width = RaspberryPiHeader.BUTTON_VIA_KEEPOUT_HALF_WIDTH_MM
        left = math.floor((cx - half_width) / grid_router.GRID_MM)
        right = math.ceil((cx + half_width) / grid_router.GRID_MM)
        near = math.floor(cy / grid_router.GRID_MM)
        far = math.ceil(
            (cy + direction * RaspberryPiHeader.BUTTON_VIA_KEEPOUT_LENGTH_MM)
            / grid_router.GRID_MM
        )
        forbidden.update(
            (x, y)
            for x in range(left, right + 1)
            for y in range(min(near, far), max(near, far) + 1)
        )
    return frozenset(forbidden)


def find_route(
    board: pcbnew.BOARD,
    net: pcbnew.NETINFO_ITEM,
    start: pcbnew.VECTOR2I,
    end: pcbnew.VECTOR2I,
    **options: Unpack[grid_router.RoutingOptions],
) -> grid_router.Route:
    """Route with chess-board-specific keep-outs applied to the base router."""
    return grid_router.find_route(
        board,
        net,
        start,
        end,
        additional_via_keepouts=_host_header_via_keepouts(board),
        **options,
    )


def soic_stagger_distance_mm(pin_number: str) -> float:
    """Stagger four adjacent 1.27 mm rows to avoid a wall of through-vias."""
    return Tca9554.signal_escape_distance_mm(pin_number)


def signal_escape(
    board: pcbnew.BOARD,
    net: pcbnew.NETINFO_ITEM,
    pad: pcbnew.PAD,
    *,
    add_via: bool = False,
) -> pcbnew.VECTOR2I:
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
    component_mpn = footprint.GetValue()
    escape_mm = catalog.signal_escape_distance_mm(component_mpn, pad.GetNumber())
    force_horizontal = catalog.uses_horizontal_signal_escape(component_mpn)
    distance = pcbnew.FromMM(escape_mm)
    if force_horizontal or abs(dx) >= abs(dy):
        escaped = pcbnew.VECTOR2I(at.x + (distance if dx >= 0 else -distance), at.y)
    else:
        escaped = pcbnew.VECTOR2I(at.x, at.y + (distance if dy >= 0 else -distance))
    kicad.add_trace(board, net, at, escaped)
    if add_via:
        kicad.add_via(board, net, escaped)
    return escaped


def nearest_tree_edges(
    nodes: Sequence[EndpointKey],
    route_points: Mapping[EndpointKey, pcbnew.VECTOR2I],
) -> Iterator[tuple[EndpointKey, EndpointKey]]:
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
    vias: list[pcbnew.PCB_VIA] = []
    layers_at_endpoint: defaultdict[tuple[int, int, int], set[int]] = defaultdict(set)
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


# Historical helper import retained for callers outside the stage objects.
_soic_stagger_distance_mm = soic_stagger_distance_mm
