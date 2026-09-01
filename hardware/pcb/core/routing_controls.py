"""Native KiCad routing for host controls, buses, and buttons."""

from __future__ import annotations

import pcbnew

from components.base import ComponentReference
from components.tactile_switch import TactileSwitchPad
from core import grid_router, kicad, sources
from core import routing_common as common
from core.nets import ButtonNet, Net


def route_control_signals(board, net_by_name, pads) -> None:
    """Route host SPI and level-shifted LED inputs as connected trees."""
    selected = [
        connection
        for connection in sources.netlist()["connections"]
        if connection["name"] in common.CONTROL_SIGNAL_NETS
    ]
    selected.sort(key=lambda connection: connection["name"])
    reserved_points = {}
    for connection in selected:
        name = connection["name"]
        net = net_by_name[name]
        reserved_points[name] = {
            tuple(node): common.signal_escape(
                board, net, pads[tuple(node)], add_via=True
            )
            for node in connection["pads"]
        }

    for connection in selected:
        name = connection["name"]
        nodes = [tuple(node) for node in connection["pads"]]
        nodes.sort(
            key=lambda node: (
                node[0] != ComponentReference.HOST_GPIO_HEADER,
                node[0],
                node[1],
            )
        )
        net = net_by_name[name]
        route_points = reserved_points[name]
        for left, right in common.nearest_tree_edges(nodes, route_points):
            start = route_points[left]
            end = route_points[right]
            try:
                route = grid_router.find_route(
                    board,
                    net,
                    start,
                    end,
                    allow_vias=True,
                )
            except RuntimeError as error:
                raise RuntimeError(f"{error}: {left} -> {right}") from error
            grid_router.apply_route(board, net, start, end, route)


def route_internal_buses(board, net_by_name, pads) -> None:
    """Route shared low-speed buses across the three internal signal layers."""
    connections = {item["name"]: item for item in sources.netlist()["connections"]}
    preferred_layer_indices = {
        Net.I2C_SDA: 0,
        Net.I2C_SCL: 1,
        Net.SENSE_IRQ: 2,
    }
    for name in (Net.I2C_SDA, Net.I2C_SCL, Net.SENSE_IRQ):
        nodes = [tuple(node) for node in connections[name]["pads"]]
        nodes.sort(
            key=lambda node: (
                node[0] != ComponentReference.HOST_GPIO_HEADER,
                node[0],
                node[1],
            )
        )
        net = net_by_name[name]
        route_points = {
            node: common.signal_escape(board, net, pads[node], add_via=True)
            for node in nodes
        }
        for left, right in common.nearest_tree_edges(nodes, route_points):
            start = route_points[left]
            end = route_points[right]
            route = grid_router.find_route(
                board,
                net,
                start,
                end,
                preferred_layer_index=preferred_layer_indices[name],
                allow_vias=True,
                layers=common.INTERNAL_SIGNAL_LAYERS,
            )
            grid_router.apply_route(board, net, start, end, route)


def route_buttons(board, net_by_name, pads) -> None:
    """Connect both switch contacts and route each control to the Pi header."""
    names = (
        ButtonNet.F3,
        ButtonNet.F4,
        ButtonNet.F5,
        ButtonNet.RESET,
        ButtonNet.PASS,
        ButtonNet.F1,
        ButtonNet.F2,
        ButtonNet.OK,
        ButtonNet.RIGHT,
        ButtonNet.LEFT,
        ButtonNet.DOWN,
        ButtonNet.UP,
    )
    connections = {item["name"]: item for item in sources.netlist()["connections"]}
    for index, name in enumerate(names):
        nodes = [tuple(node) for node in connections[name]["pads"]]
        pi = next(
            node for node in nodes if node[0] == ComponentReference.HOST_GPIO_HEADER
        )
        switch_node = next(node for node in nodes if node[0].startswith("SW"))
        module = next(
            footprint
            for footprint in board.GetFootprints()
            if footprint.GetReference() == switch_node[0]
        )
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
        kicad.add_trace(
            board,
            net,
            primary.GetPosition(),
            duplicate.GetPosition(),
            pcbnew.B_Cu,
        )
        try:
            route = grid_router.find_route(
                board,
                net,
                pads[pi].GetPosition(),
                primary.GetPosition(),
                preferred_layer_index=1 - index % 2,
            )
        except RuntimeError:
            fallback_layers = {
                ButtonNet.F1: pcbnew.In4_Cu,
                ButtonNet.LEFT: pcbnew.In4_Cu,
                ButtonNet.OK: pcbnew.In5_Cu,
                ButtonNet.DOWN: pcbnew.In5_Cu,
                ButtonNet.F3: pcbnew.In6_Cu,
                ButtonNet.RIGHT: pcbnew.In6_Cu,
            }
            signal_layers = (pcbnew.In4_Cu, pcbnew.In5_Cu, pcbnew.In6_Cu)
            preferred = fallback_layers.get(
                name, signal_layers[index % len(signal_layers)]
            )
            candidates = (preferred,) + tuple(
                layer for layer in signal_layers if layer != preferred
            )
            start = pads[pi].GetPosition()
            direction = 1 if pcbnew.ToMM(start.y) > 340.0 else -1
            launch = pcbnew.VECTOR2I(
                start.x
                + pcbnew.FromMM(0.8 if name == ButtonNet.F3 or index % 2 else -0.8),
                start.y + direction * pcbnew.FromMM(4.5),
            )
            for layer in candidates:
                try:
                    route = grid_router.find_route(
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
            kicad.add_trace(board, net, start, launch, layer)
            grid_router.apply_route(board, net, launch, primary.GetPosition(), route)
        else:
            grid_router.apply_route(
                board, net, pads[pi].GetPosition(), primary.GetPosition(), route
            )
