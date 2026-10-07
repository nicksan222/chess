"""Reserved connector corridors and multilayer fallback paths."""

import math
from dataclasses import replace

import pcbnew

from ..render.route import LAYER_IDS
from . import copper as native
from . import paths as grid_router
from .definition import NetRoute
from .engine import RoutingContext, find_route, footprint, route_options


def launch_keepouts(
    board: pcbnew.BOARD, declarations: tuple[NetRoute, ...]
) -> frozenset[tuple[int, int]]:
    forbidden: set[tuple[int, int]] = set()
    for route in declarations:
        launch = route.launch
        if launch is None:
            continue
        header = footprint(board, launch.reference)
        header_y = pcbnew.ToMM(header.GetPosition().y)
        for pad in header.Pads():
            if pad.GetNetname() != route.net.label:
                continue
            cx, cy = pcbnew.ToMM(pad.GetPosition().x), pcbnew.ToMM(pad.GetPosition().y)
            direction = 1 if cy > header_y else -1
            left = math.floor((cx - launch.keepout_half_width_mm) / grid_router.GRID_MM)
            right = math.ceil((cx + launch.keepout_half_width_mm) / grid_router.GRID_MM)
            near = math.floor(cy / grid_router.GRID_MM)
            far = math.ceil(
                (cy + direction * launch.keepout_length_mm) / grid_router.GRID_MM
            )
            forbidden.update(
                (x, y)
                for x in range(left, right + 1)
                for y in range(min(near, far), max(near, far) + 1)
            )
    return frozenset(forbidden)


def route_launched_nets(
    ctx: RoutingContext, declarations: tuple[NetRoute, ...]
) -> None:
    """Connect each declared net from its connector, with a checked fallback path."""

    board, net_by_name, pads = (
        ctx.board,
        ctx.nets_by_name,
        ctx.pads_by_endpoint,
    )
    for declaration in declarations:
        launch_choice = declaration.launch
        if launch_choice is None:
            raise ValueError("connector routing needs a launch declaration")
        ctx = replace(
            ctx, settings=replace(ctx.settings, track_width_mm=declaration.width_mm)
        )
        name = declaration.net.label
        nodes = list(ctx.endpoints_by_net[name])
        pi = next(node for node in nodes if node.reference == launch_choice.reference)
        switch_node = next(
            node for node in nodes if node.reference != launch_choice.reference
        )
        module = footprint(board, switch_node.reference)
        pattern = ctx.packages[switch_node.reference].land_pattern
        if pattern is None:
            raise ValueError("launch receiver requires a land pattern")
        numbers = tuple(
            pad.number or str(pad.pin)
            for pad in pattern.pads
            if str(pad.pin) == switch_node.pin
        )
        numbers = tuple(
            sorted(numbers, key=lambda number: (number != switch_node.pin, number))
        )
        receiver_pads = {pad.GetNumber(): pad for pad in module.Pads()}
        primary = receiver_pads[numbers[0]]
        net = net_by_name[name]
        for number in numbers[1:]:
            native.add_trace(
                board,
                net,
                primary.GetPosition(),
                receiver_pads[number].GetPosition(),
                width=declaration.width_mm,
            )
        try:
            route = find_route(
                ctx,
                net,
                pads[pi].GetPosition(),
                primary.GetPosition(),
                **route_options(ctx, declaration),
            )
        except RuntimeError:
            candidates = tuple(
                LAYER_IDS[layer] for layer in launch_choice.fallback_layers
            )
            start = pads[pi].GetPosition()
            header = footprint(board, launch_choice.reference)
            direction = 1 if start.y > header.GetPosition().y else -1
            launch = pcbnew.VECTOR2I(
                start.x + pcbnew.FromMM(launch_choice.x_offset_mm),
                start.y + direction * pcbnew.FromMM(launch_choice.length_mm),
            )
            for layer in candidates:
                try:
                    route = find_route(
                        ctx,
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
                raise RuntimeError(f"no connector fallback route for {name}")
            native.add_trace(
                board, net, start, launch, layer, width=declaration.width_mm
            )
            grid_router.apply_route(
                board, net, launch, primary.GetPosition(), route, settings=ctx.settings
            )
        else:
            grid_router.apply_route(
                board,
                net,
                pads[pi].GetPosition(),
                primary.GetPosition(),
                route,
                settings=ctx.settings,
            )
