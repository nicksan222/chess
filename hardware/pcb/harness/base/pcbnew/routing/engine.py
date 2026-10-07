"""Reusable routing mechanics; no board references, net names or product lookups."""

from __future__ import annotations

import math
from collections import defaultdict
from collections.abc import Iterator, Mapping, Sequence
from dataclasses import dataclass, replace
from enum import StrEnum
from typing import Unpack, cast

import pcbnew

from ...circuit import Circuit
from ...component import BoardComponent, ComponentDefinition
from ...connections import Endpoint
from ...net import Net
from ..escape import EscapeAxis
from ..outline import BoardOutline
from ..render.route import LAYER_IDS
from ..render.units import native_point
from . import copper as native
from . import paths as grid_router
from .definition import Bend, CopperPath, NetRoute
from .paths import RoutingOptions
from .settings import RoutingSettings


@dataclass(frozen=True)
class RoutingContext:
    board: pcbnew.BOARD
    nets_by_name: Mapping[str, pcbnew.NETINFO_ITEM]
    pads_by_endpoint: Mapping[Endpoint, pcbnew.PAD]
    endpoints_by_net: Mapping[str, tuple[Endpoint, ...]]
    via_keepouts: frozenset[tuple[int, int]]
    packages: Mapping[str, ComponentDefinition[StrEnum]]
    settings: RoutingSettings
    root_reference: str
    optional_via_nets: frozenset[str]
    outline: BoardOutline
    net_type: type[Net]


def context(
    circuit: Circuit[Net],
    board: pcbnew.BOARD,
    settings: RoutingSettings,
    root_reference: str,
    via_keepouts: frozenset[tuple[int, int]],
    optional_via_nets: frozenset[str],
) -> RoutingContext:
    if circuit.outline is None:
        raise ValueError("routing needs an outline")
    packages = {
        part.reference: cast(BoardComponent[StrEnum], part).definition
        for part in circuit.components()
    }
    pads: dict[Endpoint, pcbnew.PAD] = {}
    nodes: defaultdict[str, set[Endpoint]] = defaultdict(set)
    for footprint in board.GetFootprints():
        if footprint.GetReference() not in packages:
            continue
        for pad in footprint.Pads():
            pattern = packages[footprint.GetReference()].land_pattern
            if pattern is None:
                raise ValueError("routing needs a land pattern")
            number = next(
                str(land.pin)
                for land in pattern.pads
                if (land.number or str(land.pin)) == pad.GetNumber()
            )
            endpoint = Endpoint(footprint.GetReference(), number)
            pads[endpoint] = pad
            if pad.GetNetCode() and not pad.GetNetname().startswith("unconnected-"):
                nodes[pad.GetNetname()].add(endpoint)
    return RoutingContext(
        board,
        {net.GetNetname(): net for net in board.GetNetsByName().values()},
        pads,
        {name: tuple(sorted(members)) for name, members in sorted(nodes.items())},
        via_keepouts,
        packages,
        settings,
        root_reference,
        optional_via_nets,
        circuit.outline,
        circuit.net_type,
    )


def footprint(board: pcbnew.BOARD, reference: str) -> pcbnew.FOOTPRINT:
    """Resolve exactly one native footprint by its semantic reference."""
    matches = [
        item for item in board.GetFootprints() if item.GetReference() == reference
    ]
    if len(matches) != 1:
        raise RuntimeError(f"expected one {reference} footprint; found {len(matches)}")
    return matches[0]


def find_route(
    ctx: RoutingContext,
    net: pcbnew.NETINFO_ITEM,
    start: pcbnew.VECTOR2I,
    end: pcbnew.VECTOR2I,
    **options: Unpack[grid_router.RoutingOptions],
) -> grid_router.Route:
    """Route with declared keep-outs applied to the base router."""
    return grid_router.find_route(
        ctx.board,
        net,
        start,
        end,
        additional_via_keepouts=ctx.via_keepouts,
        settings=ctx.settings,
        **options,
    )


def signal_escape(
    ctx: RoutingContext,
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
    board = ctx.board
    at = pad.GetPosition()
    footprint = pad.GetParentFootprint()
    centre = footprint.GetPosition()
    dx, dy = (at.x - centre.x, at.y - centre.y)
    package = ctx.packages[footprint.GetReference()].routing
    escape_mm = package.signal_distance(pad.GetNumber())
    horizontal = package.signal_axis is EscapeAxis.HORIZONTAL or (
        package.signal_axis is EscapeAxis.AUTO and abs(dx) >= abs(dy)
    )
    half = pcbnew.ToMM(pad.GetSize().x if horizontal else pad.GetSize().y) / 2
    if add_via:
        escape_mm = max(escape_mm, half + ctx.settings.via_diameter_mm / 2 + 0.2)
    distance = pcbnew.FromMM(escape_mm)
    if horizontal:
        escaped = pcbnew.VECTOR2I(at.x + (distance if dx >= 0 else -distance), at.y)
    else:
        escaped = pcbnew.VECTOR2I(at.x, at.y + (distance if dy >= 0 else -distance))
    native.add_trace(board, net, at, escaped, width=ctx.settings.track_width_mm)
    if add_via:
        native.add_via(
            board, net, escaped, ctx.settings.via_diameter_mm, ctx.settings.via_drill_mm
        )
    return escaped


def nearest_tree_edges(
    nodes: Sequence[Endpoint],
    route_points: Mapping[Endpoint, pcbnew.VECTOR2I],
) -> Iterator[tuple[Endpoint, Endpoint]]:
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


def prune_unused_signal_vias(ctx: RoutingContext) -> None:
    """Remove optional escape vias from routes that stayed on one layer."""
    board = ctx.board
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
        if name not in ctx.optional_via_nets:
            continue
        at = via.GetPosition()
        key = (via.GetNetCode(), at.x, at.y)
        if len(layers_at_endpoint[key]) < 2:
            board.Remove(via)


def escape_endpoint(
    ctx: RoutingContext,
    name: str,
    endpoint: Endpoint,
    *,
    add_via: bool = False,
) -> pcbnew.VECTOR2I:
    """Escape one connection endpoint (see `signal_escape`); returns where routing resumes."""
    return signal_escape(
        ctx,
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
    """Search and apply a route with the declared keepouts."""
    route = find_route(ctx, net, start, end, **options)
    grid_router.apply_route(ctx.board, net, start, end, route, settings=ctx.settings)


def ordered_endpoints(ctx: RoutingContext, connection: str) -> list[Endpoint]:
    """Endpoints of a net in a deterministic order, declared root first (so trees grow from it)."""
    return sorted(
        ctx.endpoints_by_net[connection],
        key=lambda node: (
            node.reference != ctx.root_reference,
            node.reference,
            node.pin,
        ),
    )


def reserve_escape_points(
    ctx: RoutingContext, connection: str, endpoints: Sequence[Endpoint]
) -> dict[Endpoint, pcbnew.VECTOR2I]:
    """Lay every endpoint's escape stub and via up front, so later routes treat them as obstacles.

    Reserving all of a net's escapes before routing any of its edges keeps a route from passing
    where another endpoint's via will stand.
    """
    return {
        endpoint: escape_endpoint(ctx, connection, endpoint, add_via=True)
        for endpoint in endpoints
    }


def route_tree(
    ctx: RoutingContext,
    connection: str,
    nodes: Sequence[Endpoint],
    route_points: Mapping[Endpoint, pcbnew.VECTOR2I],
    *,
    label_errors: bool = False,
    **options: Unpack[RoutingOptions],
) -> None:
    """Connect `nodes` into one tree with nearest-neighbour edges, routing each edge.

    `route_points` gives each node's start point (usually its escape end). `options` pass to the
    grid router (layers, vias, preferred layer). With `label_errors`, a failure names the pair.
    """
    net = ctx.nets_by_name[connection]
    for left, right in nearest_tree_edges(nodes, route_points):
        try:
            route_between(ctx, net, route_points[left], route_points[right], **options)
        except RuntimeError as error:
            if label_errors:
                raise RuntimeError(f"{error}: {left} -> {right}") from error
            raise


def route_options(ctx: RoutingContext, declaration: NetRoute) -> RoutingOptions:
    layers = tuple(LAYER_IDS[layer] for layer in declaration.layers)
    options: RoutingOptions = {
        "layers": layers,
        "allow_vias": declaration.allow_vias,
        "diagonals": declaration.diagonals,
    }
    if declaration.preferred_layer is not None:
        options["preferred_layer_index"] = declaration.layers.index(
            declaration.preferred_layer
        )
    if declaration.area is not None:
        left, bottom, right, top = declaration.area
        from ..point import Point

        a = native_point(Point(left, top), ctx.outline)
        b = native_point(Point(right, bottom), ctx.outline)
        options["routing_bounds_mm"] = (
            pcbnew.ToMM(a.x),
            pcbnew.ToMM(a.y),
            pcbnew.ToMM(b.x),
            pcbnew.ToMM(b.y),
        )
    return options


def reserve_routes(
    ctx: RoutingContext, declarations: Sequence[NetRoute]
) -> dict[str, dict[Endpoint, pcbnew.VECTOR2I]]:
    points: dict[str, dict[Endpoint, pcbnew.VECTOR2I]] = {}
    for route in declarations:
        current = replace(
            ctx, settings=replace(ctx.settings, track_width_mm=route.width_mm)
        )
        overrides = dict(route.escapes)
        points[route.net.label] = {
            endpoint: native_point(overrides[endpoint], ctx.outline)
            if endpoint in overrides
            else escape_endpoint(current, route.net.label, endpoint, add_via=True)
            for endpoint in route_endpoints(ctx, route)
        }
    return points


def route_nets(
    ctx: RoutingContext,
    declarations: Sequence[NetRoute],
    *,
    reserved: Mapping[str, Mapping[Endpoint, pcbnew.VECTOR2I]] | None = None,
    reserve_together: bool = False,
) -> None:
    points = (
        reserved
        if reserved is not None
        else reserve_routes(ctx, declarations)
        if reserve_together
        else {}
    )
    for route in declarations:
        current = replace(
            ctx, settings=replace(ctx.settings, track_width_mm=route.width_mm)
        )
        name = route.net.label
        nodes = route_endpoints(ctx, route)
        escapes = (
            points[name]
            if name in points
            else reserve_escape_points(current, name, nodes)
        )
        route_tree(
            current,
            name,
            nodes,
            escapes,
            label_errors=True,
            **route_options(ctx, route),
        )


def apply_paths(ctx: RoutingContext, paths: Sequence[CopperPath]) -> None:
    from itertools import pairwise

    from ..point import Point

    for path in paths:
        if type(path.net) is not ctx.net_type:
            raise ValueError("copper path must use the circuit's net enum")
        points: list[pcbnew.VECTOR2I] = []
        for anchor in path.points:
            if isinstance(anchor, Point):
                points.append(native_point(anchor, ctx.outline))
            else:
                pad = ctx.pads_by_endpoint[anchor]
                if pad.GetNetname() != path.net.label:
                    raise ValueError(
                        f"{anchor.reference}/{anchor.pin}: path would change the pin's net"
                    )
                points.append(pad.GetPosition())
        if path.bend is not None:
            start, end = points
            corner = (
                pcbnew.VECTOR2I(end.x, start.y)
                if path.bend is Bend.HORIZONTAL_FIRST
                else pcbnew.VECTOR2I(start.x, end.y)
            )
            points.insert(1, corner)
        for start, end in pairwise(points):
            native.add_trace(
                ctx.board,
                ctx.nets_by_name[path.net.label],
                start,
                end,
                LAYER_IDS[path.layer],
                path.width_mm,
            )


def fanout_power(
    ctx: RoutingContext, rail_names: frozenset[str], excluded_references: frozenset[str]
) -> None:
    board, net_by_name = (ctx.board, ctx.nets_by_name)
    for module in board.GetFootprints():
        # Board-owned exact copper can replace automatic package fanout.
        if module.GetReference() in excluded_references:
            continue
        for pad in module.Pads():
            name = pad.GetNetname()
            if pad.GetAttribute() != pcbnew.PAD_ATTRIB_SMD or name not in rail_names:
                continue
            at = pad.GetPosition()
            package = ctx.packages[module.GetReference()].routing
            pattern = ctx.packages[module.GetReference()].land_pattern
            assert pattern is not None
            logical_pin = next(
                land.pin
                for land in pattern.pads
                if land.physical_number == pad.GetNumber()
            )
            if any(path.pin == logical_pin for path in package.paths):
                continue
            escaped = _power_escape_position(ctx, module, pad)
            net = net_by_name[name]
            if ctx.packages[module.GetReference()].routing.power_via_count > 1:
                _fault_fanout(ctx, module.GetReference(), net, at, escaped)
                continue
            native.add_trace(board, net, at, escaped, width=package.power_width_mm)
            native.add_via(
                board,
                net,
                escaped,
                ctx.settings.via_diameter_mm,
                ctx.settings.via_drill_mm,
            )


def _fault_fanout(
    ctx: RoutingContext,
    reference: str,
    net: pcbnew.NETINFO_ITEM,
    at: pcbnew.VECTOR2I,
    escaped: pcbnew.VECTOR2I,
) -> None:
    """A wide stub into a row of vias across the escape direction."""
    board = ctx.board
    package = ctx.packages[reference].routing
    width = package.power_width_mm
    pitch = pcbnew.FromMM(package.power_via_pitch_mm)
    across_x = escaped.y != at.y
    span = (package.power_via_count - 1) // 2
    row = [
        pcbnew.VECTOR2I(
            escaped.x + (step * pitch if across_x else 0),
            escaped.y + (0 if across_x else step * pitch),
        )
        for step in range(-span, span + 1)
    ]
    native.add_trace(board, net, at, escaped, width=width)
    native.add_trace(board, net, row[0], row[-1], width=width)
    for point in row:
        native.add_via(
            board, net, point, ctx.settings.via_diameter_mm, ctx.settings.via_drill_mm
        )


def _power_escape_position(
    ctx: RoutingContext, module: pcbnew.FOOTPRINT, pad: pcbnew.PAD
) -> pcbnew.VECTOR2I:
    """Choose a short fanout that clears its package and nearby signal lanes."""
    at = pad.GetPosition()
    centre = module.GetPosition()
    dx = at.x - centre.x
    dy = at.y - centre.y
    package = ctx.packages[module.GetReference()].routing
    escape_mm = package.power_distance(pad.GetNumber())
    horizontal = package.power_axis is EscapeAxis.HORIZONTAL
    vertical = package.power_axis is EscapeAxis.VERTICAL
    # Escape along one axis, far enough that the via never enters the pad's mask.
    if horizontal or (not vertical and abs(dx) >= abs(dy)):
        half = pcbnew.ToMM(pad.GetSize().x) / 2
        reach = max(escape_mm, half + (ctx.settings.via_diameter_mm / 2 + 0.2))
        distance = pcbnew.FromMM(reach)
        return pcbnew.VECTOR2I(at.x + (distance if dx >= 0 else -distance), at.y)
    half = pcbnew.ToMM(pad.GetSize().y) / 2
    distance = pcbnew.FromMM(
        max(escape_mm, half + (ctx.settings.via_diameter_mm / 2 + 0.2))
    )
    return pcbnew.VECTOR2I(at.x, at.y + (distance if dy >= 0 else -distance))


def route_plan(ctx: RoutingContext, declarations: tuple[NetRoute, ...]) -> None:
    """Reserve local exits early, then route priority groups in declaration order."""
    from .launch import route_launched_nets

    # Reserve declared package exits before any priority group occupies their copper.
    early = tuple(
        route
        for route in declarations
        if route.launch is None and (route.area is not None or route.reserve_group)
    )
    reserved = reserve_routes(ctx, early)
    for priority in sorted({route.priority for route in declarations}):
        group = tuple(route for route in declarations if route.priority == priority)
        points = dict(reserved)
        if any(route.reserve_group for route in group):
            pending = tuple(
                route
                for route in group
                if route.launch is None and route.net.label not in points
            )
            points.update(reserve_routes(ctx, pending))
        keepouts: set[tuple[int, int]] = set(ctx.via_keepouts)
        for route in group:
            radius = route.via_keepout_mm
            if radius <= 0:
                continue
            nodes = route_endpoints(ctx, route)
            spots = [
                *points[route.net.label].values(),
                *(ctx.pads_by_endpoint[node].GetPosition() for node in nodes),
            ]
            span = range(
                -math.ceil(radius / grid_router.GRID_MM),
                math.ceil(radius / grid_router.GRID_MM) + 1,
            )
            for spot in spots:
                x, y = pcbnew.ToMM(spot.x), pcbnew.ToMM(spot.y)
                keepouts.update(
                    (
                        round(x / grid_router.GRID_MM) + i,
                        round(y / grid_router.GRID_MM) + j,
                    )
                    for i in span
                    for j in span
                    if math.hypot(i * grid_router.GRID_MM, j * grid_router.GRID_MM)
                    <= radius
                )
        current = replace(ctx, via_keepouts=frozenset(keepouts))
        for route in group:
            if route.launch is not None:
                route_launched_nets(current, (route,))
            else:
                route_nets(current, (route,), reserved=points)


def route_endpoints(ctx: RoutingContext, route: NetRoute) -> list[Endpoint]:
    nodes = (
        list(ctx.endpoints_by_net[route.net.label])
        if route.area is not None
        else ordered_endpoints(ctx, route.net.label)
    )
    if any(
        endpoint not in nodes
        for endpoint in (*route.omit, *(endpoint for endpoint, _ in route.escapes))
    ):
        raise ValueError("route endpoint must belong to its net")
    nodes = [endpoint for endpoint in nodes if endpoint not in route.omit]
    if route.last_reference is not None:
        nodes.sort(key=lambda endpoint: endpoint.reference == route.last_reference)
    return nodes
