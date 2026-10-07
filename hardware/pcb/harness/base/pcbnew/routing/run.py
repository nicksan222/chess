"""Execute circuit-owned routing declarations through the native KiCad adapter."""

from enum import StrEnum
from functools import partial
from itertools import pairwise
from typing import cast

import pcbnew

from ...circuit import Circuit
from ...component import BoardComponent
from ...geometry import Side
from ...net import Net
from ..render.units import native_point
from . import copper
from .circuit import route_circuit
from .definition import DirectLink, RoutingPlan, validate_routes
from .engine import (
    RoutingContext,
    apply_paths,
    context,
    fanout_power,
    prune_unused_signal_vias,
    route_between,
    route_plan,
)
from .launch import launch_keepouts
from .settings import RoutingSettings
from .width import split_package_escapes


def route[BoardNet: Net](
    circuit: Circuit[BoardNet], plan: RoutingPlan, settings: RoutingSettings
) -> None:
    references = {part.reference for part in circuit.components()}
    if (
        plan.root_reference not in references
        or not set(plan.power_exclusions) <= references
    ):
        raise ValueError("routing plan must select components from this circuit")
    if any(type(net) is not circuit.net_type for net in plan.power_nets):
        raise ValueError("power fanout must use circuit's net enum")
    nets = tuple(net for stage in plan.stages for net in stage.nets)
    validate_routes(circuit.net_type, nets)
    route_circuit(circuit, partial(_apply, cast(Circuit[Net], circuit), plan, settings))


def _apply(
    circuit: Circuit[Net],
    plan: RoutingPlan,
    settings: RoutingSettings,
    board: pcbnew.BOARD,
) -> None:
    nets = tuple(net for stage in plan.stages for net in stage.nets)
    ctx = context(
        circuit,
        board,
        settings,
        plan.root_reference,
        launch_keepouts(board, nets),
        frozenset(net.net.label for net in nets if net.prune_unused_vias),
    )
    fanout_power(
        ctx,
        frozenset(net.label for net in plan.power_nets),
        frozenset(plan.power_exclusions),
    )
    # Package geometry is transformed from the actual instance, never a reference table.
    for placed in circuit.components():
        component = cast(BoardComponent[StrEnum], placed)
        for path in component.definition.routing.paths:
            net = ctx.nets_by_name[component.net(path.pin).label]
            points = tuple(
                native_point(component.local_point(point.x_mm, point.y_mm), ctx.outline)
                for point in path.points
            )
            for start, end in pairwise(points):
                copper.add_trace(
                    board,
                    net,
                    start,
                    end,
                    pcbnew.B_Cu
                    if component.placement.side is Side.BOTTOM
                    else pcbnew.F_Cu,
                    width=path.width_mm,
                )
            if path.via:
                copper.add_via(
                    board,
                    net,
                    points[-1],
                    settings.via_diameter_mm,
                    settings.via_drill_mm,
                )
        for via in component.definition.routing.vias:
            copper.add_via(
                board,
                ctx.nets_by_name[component.net(via.pin).label],
                native_point(
                    component.local_point(via.center.x_mm, via.center.y_mm), ctx.outline
                ),
                settings.via_diameter_mm,
                settings.via_drill_mm,
            )
    deferred: list[DirectLink] = []
    for stage in plan.stages:
        apply_paths(ctx, stage.paths)
        for via in stage.vias:
            if type(via.net) is not circuit.net_type:
                raise ValueError("via must use circuit's net enum")
            copper.add_via(
                board,
                ctx.nets_by_name[via.net.label],
                native_point(via.center, ctx.outline),
                via.diameter_mm,
                via.drill_mm,
            )
        for link in stage.links:
            if not _direct_link(ctx, link):
                deferred.append(link)
        route_plan(ctx, stage.nets)
    for link in deferred:
        route_between(
            ctx,
            ctx.nets_by_name[link.net.label],
            ctx.pads_by_endpoint[link.start].GetPosition(),
            ctx.pads_by_endpoint[link.end].GetPosition(),
            preferred_layer_index=0,
            required_end_layer_index=0,
        )
    prune_unused_signal_vias(ctx)
    for placed in circuit.components():
        component = cast(BoardComponent[StrEnum], placed)
        if component.definition.routing.clearance is not None:
            split_package_escapes(board, component, settings.track_width_mm)


def _direct_link(ctx: RoutingContext, link: DirectLink) -> bool:
    if type(link.net) is not ctx.net_type:
        raise ValueError("direct link must use circuit's net enum")
    pads = (ctx.pads_by_endpoint[link.start], ctx.pads_by_endpoint[link.end])
    if any(pad.GetNetname() != link.net.label for pad in pads):
        raise ValueError("direct link cannot change a pin's net")
    start, end = (pad.GetPosition() for pad in pads)
    if start.y != end.y:
        raise ValueError("direct links require aligned pads")
    x0, x1 = sorted((start.x, end.x))
    for footprint in ctx.board.GetFootprints():
        if footprint.GetReference() in (link.start.reference, link.end.reference):
            continue
        box = footprint.GetBoundingBox()
        if (
            box.GetLeft() <= x1
            and box.GetRight() >= x0
            and box.GetTop() <= start.y <= box.GetBottom()
        ):
            return False
    copper.add_trace(
        ctx.board,
        ctx.nets_by_name[link.net.label],
        start,
        end,
        width=ctx.settings.track_width_mm,
    )
    return True
