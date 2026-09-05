"""Ordered chessboard routing policies, sharing one native copper state."""

from __future__ import annotations

import math
from collections import defaultdict
from collections.abc import Iterator, Mapping, Sequence
from dataclasses import dataclass
from typing import Unpack

import pcbnew

import pcb.definition.assemblies.sensing as hall_banks
import pcb.definition.routing.paths as grid_router
from pcb.definition import native, rules
from pcb.definition.native import EndpointKey
from pcb.definition.parts import catalog
from pcb.definition.parts.catalog import (
    DC_INPUT_JACK,
    INPUT_FUSE,
    MAIN_POWER_SWITCH,
    RASPBERRYPIHEADER_BUTTON_VIA_KEEPOUT_HALF_WIDTH_MM,
    RASPBERRYPIHEADER_BUTTON_VIA_KEEPOUT_LENGTH_MM,
    RASPBERRYPIHEADER_POWER_ESCAPE_MM,
)
from pcb.definition.routing.paths import RoutingOptions
from pcb.definition.rules import Net
from shared import wiring
from shared.dimensions import PLAYING_SPAN_MM, SQUARE_SIZE_MM
from shared.electronics import (
    BarrelJackPin,
    ComponentReference,
    FusePin,
    PowerSwitchPin,
    Sk9822Pin,
    TactileSwitchPad,
)
from shared.electronics import Sk9822Component as Sk9822
from shared.electronics import Tca9554Component as Tca9554
from shared.hall_banks import BANK_FILES, BANK_RANKS, HallBank

INTERNAL_SIGNAL_LAYERS = (pcbnew.In4_Cu, pcbnew.In5_Cu, pcbnew.In6_Cu)

SENSOR_ROUTING_LAYERS = (pcbnew.F_Cu, pcbnew.B_Cu, *INTERNAL_SIGNAL_LAYERS)

CONTROL_SIGNAL_NETS = frozenset(
    {
        wiring.SPI_CLOCK_NET,
        wiring.SPI_DATA_NET,
        wiring.LED_CLOCK_NET,
        wiring.LED_DATA_NET,
    }
)
BUTTON_NETS = frozenset(map(wiring.button_net, wiring.BUTTON_NAMES))

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
        if pad.GetNetname() not in BUTTON_NETS:
            continue
        centre = pad.GetPosition()
        cx, cy = (pcbnew.ToMM(centre.x), pcbnew.ToMM(centre.y))
        direction = 1 if cy > header_y else -1
        half_width = RASPBERRYPIHEADER_BUTTON_VIA_KEEPOUT_HALF_WIDTH_MM
        left = math.floor((cx - half_width) / grid_router.GRID_MM)
        right = math.ceil((cx + half_width) / grid_router.GRID_MM)
        near = math.floor(cy / grid_router.GRID_MM)
        far = math.ceil(
            (cy + direction * RASPBERRYPIHEADER_BUTTON_VIA_KEEPOUT_LENGTH_MM)
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
    dx, dy = (at.x - centre.x, at.y - centre.y)
    component_mpn = footprint.GetValue()
    escape_mm = catalog.signal_escape_distance_mm(component_mpn, pad.GetNumber())
    force_horizontal = catalog.uses_horizontal_signal_escape(component_mpn)
    distance = pcbnew.FromMM(escape_mm)
    if force_horizontal or abs(dx) >= abs(dy):
        escaped = pcbnew.VECTOR2I(at.x + (distance if dx >= 0 else -distance), at.y)
    else:
        escaped = pcbnew.VECTOR2I(at.x, at.y + (distance if dy >= 0 else -distance))
    native.add_trace(board, net, at, escaped)
    if add_via:
        native.add_via(board, net, escaped)
    return escaped


def nearest_tree_edges(
    nodes: Sequence[EndpointKey], route_points: Mapping[EndpointKey, pcbnew.VECTOR2I]
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
        yield (nodes[left], nodes[right])
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


@dataclass(frozen=True)
class RoutingContext:
    """Lookup caches over native objects for the lifetime of a routing pass."""

    board: pcbnew.BOARD
    nets_by_name: Mapping[str, pcbnew.NETINFO_ITEM]
    pads_by_endpoint: Mapping[EndpointKey, pcbnew.PAD]
    endpoints_by_net: Mapping[str, tuple[EndpointKey, ...]]


def escape_endpoint(
    ctx: RoutingContext, name: str, endpoint: EndpointKey, *, add_via: bool = False
) -> pcbnew.VECTOR2I:
    return signal_escape(
        ctx.board,
        ctx.nets_by_name[name],
        ctx.pads_by_endpoint[endpoint],
        add_via=add_via,
    )


def route_between(
    ctx: RoutingContext,
    net: pcbnew.NETINFO_ITEM,
    start: pcbnew.VECTOR2I,
    end: pcbnew.VECTOR2I,
    **options: Unpack[grid_router.RoutingOptions],
) -> None:
    """Search and apply a route with the common chess-board keepouts."""
    route = find_route(ctx.board, net, start, end, **options)
    grid_router.apply_route(ctx.board, net, start, end, route)


def ordered_endpoints(ctx: RoutingContext, connection: str) -> list[EndpointKey]:
    return sorted(
        ctx.endpoints_by_net[connection],
        key=lambda node: (
            node[0] != ComponentReference.HOST_GPIO_HEADER,
            node[0],
            node[1],
        ),
    )


def reserve_escape_points(
    ctx: RoutingContext, connection: str, endpoints: Sequence[EndpointKey]
) -> dict[EndpointKey, pcbnew.VECTOR2I]:
    return {
        endpoint: escape_endpoint(ctx, connection, endpoint, add_via=True)
        for endpoint in endpoints
    }


def route_tree(
    ctx: RoutingContext,
    connection: str,
    nodes: Sequence[EndpointKey],
    route_points: Mapping[EndpointKey, pcbnew.VECTOR2I],
    *,
    label_errors: bool = False,
    **options: Unpack[RoutingOptions],
) -> None:
    net = ctx.nets_by_name[connection]
    for left, right in nearest_tree_edges(nodes, route_points):
        try:
            route_between(ctx, net, route_points[left], route_points[right], **options)
        except RuntimeError as error:
            if label_errors:
                raise RuntimeError(f"{error}: {left} -> {right}") from error
            raise


def route_control_signals(ctx: RoutingContext) -> None:
    selected = sorted(
        (
            connection
            for connection in ctx.endpoints_by_net
            if connection in CONTROL_SIGNAL_NETS
        ),
        key=lambda connection: connection,
    )
    reserved_points = {
        connection: reserve_escape_points(
            ctx, connection, ctx.endpoints_by_net[connection]
        )
        for connection in selected
    }
    for connection in selected:
        route_tree(
            ctx,
            connection,
            ordered_endpoints(ctx, connection),
            reserved_points[connection],
            allow_vias=True,
            label_errors=True,
        )


def route_internal_buses(ctx: RoutingContext) -> None:
    for layer_index, name in enumerate((wiring.SDA_NET, wiring.SCL_NET)):
        connection = name
        nodes = ordered_endpoints(ctx, connection)
        route_tree(
            ctx,
            connection,
            nodes,
            reserve_escape_points(ctx, connection, nodes),
            preferred_layer_index=layer_index,
            allow_vias=True,
            layers=INTERNAL_SIGNAL_LAYERS,
        )


def route_buttons(ctx: RoutingContext) -> None:
    board, net_by_name, pads = (
        ctx.board,
        ctx.nets_by_name,
        ctx.pads_by_endpoint,
    )
    names = tuple(
        map(
            wiring.button_net,
            (
                "F3",
                "F4",
                "F5",
                "RESET",
                "PASS",
                "F1",
                "F2",
                "OK",
                "RIGHT",
                "LEFT",
                "DOWN",
                "UP",
            ),
        )
    )
    for index, name in enumerate(names):
        nodes = list(ctx.endpoints_by_net[name])
        pi = next(
            node for node in nodes if node[0] == ComponentReference.HOST_GPIO_HEADER
        )
        switch_node = next(node for node in nodes if node[0].startswith("SW"))
        module = footprint(board, switch_node[0])
        primary = next(
            pad
            for pad in module.Pads()
            if pad.GetNumber() == TactileSwitchPad.SIGNAL_PRIMARY
        )
        duplicate = next(
            pad
            for pad in module.Pads()
            if pad.GetNumber() == TactileSwitchPad.SIGNAL_DUPLICATE
        )
        net = net_by_name[name]
        native.add_trace(
            board, net, primary.GetPosition(), duplicate.GetPosition(), pcbnew.B_Cu
        )
        try:
            route = find_route(
                board,
                net,
                pads[pi].GetPosition(),
                primary.GetPosition(),
                preferred_layer_index=1 - index % 2,
            )
        except RuntimeError:
            fallback_layers = {
                wiring.button_net("F1"): pcbnew.In4_Cu,
                wiring.button_net("LEFT"): pcbnew.In4_Cu,
                wiring.button_net("OK"): pcbnew.In5_Cu,
                wiring.button_net("DOWN"): pcbnew.In5_Cu,
                wiring.button_net("F3"): pcbnew.In6_Cu,
                wiring.button_net("RIGHT"): pcbnew.In6_Cu,
            }
            signal_layers = (pcbnew.In4_Cu, pcbnew.In5_Cu, pcbnew.In6_Cu)
            preferred = fallback_layers.get(
                name, signal_layers[index % len(signal_layers)]
            )
            candidates = (preferred,) + tuple(
                layer for layer in signal_layers if layer != preferred
            )
            start = pads[pi].GetPosition()
            header = footprint(board, ComponentReference.HOST_GPIO_HEADER)
            direction = 1 if start.y > header.GetPosition().y else -1
            launch = pcbnew.VECTOR2I(
                start.x
                + pcbnew.FromMM(
                    0.8 if name == wiring.button_net("F3") or index % 2 else -0.8
                ),
                start.y + direction * pcbnew.FromMM(4.5),
            )
            for layer in candidates:
                try:
                    route = find_route(
                        board,
                        net,
                        launch,
                        primary.GetPosition(),
                        preferred_layer_index=0,
                        allow_vias=False,
                        layers=(layer,),
                        diagonals=True,
                    )
                    break
                except RuntimeError:
                    continue
            else:
                raise RuntimeError(f"no internal button route for {name}")
            native.add_trace(board, net, start, launch, layer)
            grid_router.apply_route(board, net, launch, primary.GetPosition(), route)
        else:
            grid_router.apply_route(
                board, net, pads[pi].GetPosition(), primary.GetPosition(), route
            )


def route_led_chain(ctx: RoutingContext, *, obstructed_only: bool = False) -> None:
    board, net_by_name, pads = (
        ctx.board,
        ctx.nets_by_name,
        ctx.pads_by_endpoint,
    )
    origin = native.point(0.0, 0.0).x
    for connection in ctx.endpoints_by_net:
        nodes = list(ctx.endpoints_by_net[connection])
        if len(nodes) != 2 or not all(
            node in pads and node[0].startswith("U") for node in nodes
        ):
            continue
        if nodes[0][1] in Sk9822.input_pins() and nodes[1][1] in Sk9822.output_pins():
            nodes.reverse()
        if (
            nodes[0][1] not in Sk9822.output_pins()
            or nodes[1][1] not in Sk9822.input_pins()
        ):
            continue
        name = connection
        net = net_by_name[name]
        start, end = (pads[node].GetPosition() for node in nodes)
        c0, c1 = (pads[node].GetParent().GetPosition() for node in nodes)
        if c0.y == c1.y:
            x0, x1 = sorted((start.x, end.x))
            blocker = next(
                (
                    module.GetBoundingBox()
                    for module in board.GetFootprints()
                    if module.GetReference() not in {nodes[0][0], nodes[1][0]}
                    and module.GetBoundingBox().GetLeft() <= x1
                    and (module.GetBoundingBox().GetRight() >= x0)
                    and (
                        module.GetBoundingBox().GetTop()
                        <= start.y
                        <= module.GetBoundingBox().GetBottom()
                    )
                ),
                None,
            )
            if blocker is None:
                if not obstructed_only:
                    native.add_trace(board, net, start, end)
                continue
            if obstructed_only:
                route_between(
                    ctx,
                    net,
                    start,
                    end,
                    preferred_layer_index=0,
                    required_end_layer_index=0,
                )
            continue
        if obstructed_only:
            continue
        right_side = start.x > origin
        direction = 1 if right_side else -1
        is_clock = nodes[0][1] == Sk9822Pin.CLOCK_OUT
        distance_mm = (
            (3.0 if right_side else 8.0) if is_clock else 1.0 if right_side else 6.0
        )
        distance = pcbnew.FromMM(distance_mm)
        first = pcbnew.VECTOR2I(start.x + direction * distance, start.y)
        second = pcbnew.VECTOR2I(end.x + direction * distance, end.y)
        if is_clock:
            native.add_trace(board, net, start, first)
            native.add_trace(board, net, first, second)
            native.add_trace(board, net, second, end)
        else:
            native.add_trace(board, net, start, first)
            native.add_trace(board, net, second, end)
            native.add_via(board, net, first)
            native.add_via(board, net, second)
            native.add_trace(board, net, first, second, pcbnew.B_Cu)


def route_input_power(ctx: RoutingContext) -> None:
    board, net_by_name, pads = (
        ctx.board,
        ctx.nets_by_name,
        ctx.pads_by_endpoint,
    )
    routes = (
        (
            Net.DC_INPUT,
            DC_INPUT_JACK.endpoint(BarrelJackPin.CENTRE_POSITIVE),
            INPUT_FUSE.endpoint(FusePin.UNFUSED_INPUT),
            -183.0,
        ),
        (
            Net.DC_FUSED,
            INPUT_FUSE.endpoint(FusePin.FUSED_OUTPUT),
            MAIN_POWER_SWITCH.endpoint(PowerSwitchPin.FUSED_INPUT),
            -194.0,
        ),
    )
    for name, left, right, lane_y in routes:
        net = net_by_name[name]
        start, end = (pads[left].GetPosition(), pads[right].GetPosition())
        native_y = native.point(0.0, lane_y).y
        first = pcbnew.VECTOR2I(start.x, native_y)
        second = pcbnew.VECTOR2I(end.x, native_y)
        native.add_trace(board, net, start, first, width=rules.POWER_TRACE_WIDTH_MM)
        native.add_trace(board, net, first, second, width=rules.POWER_TRACE_WIDTH_MM)
        native.add_trace(board, net, second, end, width=rules.POWER_TRACE_WIDTH_MM)


def fanout_power(ctx: RoutingContext) -> None:
    board, net_by_name = (ctx.board, ctx.nets_by_name)
    rail_names = {Net.GROUND, Net.FIVE_VOLTS, Net.THREE_VOLTS_THREE}
    for module in board.GetFootprints():
        for pad in module.Pads():
            name = pad.GetNetname()
            if pad.GetAttribute() != pcbnew.PAD_ATTRIB_SMD or name not in rail_names:
                continue
            at = pad.GetPosition()
            escaped = _power_escape_position(module, pad)
            net = net_by_name[name]
            native.add_trace(board, net, at, escaped)
            native.add_via(board, net, escaped)


def _power_escape_position(
    module: pcbnew.FOOTPRINT, pad: pcbnew.PAD
) -> pcbnew.VECTOR2I:
    """Choose a short fanout that clears its package and nearby signal lanes."""
    at = pad.GetPosition()
    centre = module.GetPosition()
    dx, dy = (at.x - centre.x, at.y - centre.y)
    reference = module.GetReference()
    if reference == ComponentReference.HOST_GPIO_HEADER:
        escape_mm, horizontal = (RASPBERRYPIHEADER_POWER_ESCAPE_MM, True)
    else:
        escape_mm, horizontal = catalog.power_escape_policy(
            module.GetValue(), pad.GetNumber()
        )
    distance = pcbnew.FromMM(escape_mm)
    if horizontal:
        escaped = pcbnew.VECTOR2I(at.x + (distance if dx >= 0 else -distance), at.y)
    else:
        length = max(1, round((dx * dx + dy * dy) ** 0.5))
        escaped = pcbnew.VECTOR2I(
            at.x + dx * distance // length, at.y + dy * distance // length
        )
    return escaped


BANK_ROUTE_INSET_MM = 1.0


@dataclass(frozen=True)
class PendingHallRoute:
    """Exact native escape endpoints and the bank's centre-line corridor."""

    net: pcbnew.NETINFO_ITEM
    start: pcbnew.VECTOR2I
    end: pcbnew.VECTOR2I
    bounds_mm: tuple[float, float, float, float]


def _bank_routing_bounds_mm(bank: HallBank) -> tuple[float, float, float, float]:
    """Convert shared Y-up bank geometry to native (left, top, right, bottom)."""
    cx, cy = bank.centre(SQUARE_SIZE_MM, PLAYING_SPAN_MM)
    half_x = BANK_FILES * SQUARE_SIZE_MM / 2 - BANK_ROUTE_INSET_MM
    half_y = BANK_RANKS * SQUARE_SIZE_MM / 2 - BANK_ROUTE_INSET_MM
    top_left = native.point(cx - half_x, cy + half_y)
    bottom_right = native.point(cx + half_x, cy - half_y)
    return (
        pcbnew.ToMM(top_left.x),
        pcbnew.ToMM(top_left.y),
        pcbnew.ToMM(bottom_right.x),
        pcbnew.ToMM(bottom_right.y),
    )


def reserve_hall(ctx: RoutingContext) -> list[PendingHallRoute]:
    """Reserve bank/address/port escapes before shared buses add obstacles."""
    pending: list[PendingHallRoute] = []
    for bank, (ref, _) in zip(
        hall_banks.dimensions.HALL_BANKS, hall_banks.BANK_REFERENCES, strict=True
    ):
        bounds = _bank_routing_bounds_mm(bank)
        for pin in Tca9554.input_pins():
            name = ctx.pads_by_endpoint[ref, pin].GetNetname()
            start, end = (
                escape_endpoint(ctx, name, endpoint, add_via=True)
                for endpoint in ctx.endpoints_by_net[name]
            )
            pending.append(PendingHallRoute(ctx.nets_by_name[name], start, end, bounds))
    return pending


def route_hall(ctx: RoutingContext, pending: list[PendingHallRoute]) -> None:
    """Keep every reserved signal inside its own bank, never its neighbour."""
    for pending_route in pending:
        route_between(
            ctx,
            pending_route.net,
            pending_route.start,
            pending_route.end,
            layers=SENSOR_ROUTING_LAYERS,
            diagonals=True,
            routing_bounds_mm=pending_route.bounds_mm,
        )


def route(board: pcbnew.BOARD) -> None:
    """Route copper in dependency order so later passes respect earlier paths."""
    nodes = native.connections(board)
    ctx = RoutingContext(
        board,
        {n.GetNetname(): n for n in board.GetNetsByName().values()},
        native.endpoint_pads(board),
        nodes,
    )
    fanout_power(ctx)
    route_led_chain(ctx)
    route_control_signals(ctx)
    pending = reserve_hall(ctx)
    route_buttons(ctx)
    route_internal_buses(ctx)
    route_hall(ctx, pending)
    route_led_chain(ctx, obstructed_only=True)
    route_input_power(ctx)
    prune_unused_signal_vias(ctx.board)
