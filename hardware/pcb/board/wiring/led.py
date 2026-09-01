"""Native KiCad routing for the serpentine SK9822 chain."""

from __future__ import annotations

from base.kicad import board as kicad
from base.kicad import grid_router
from base.kicad.api import pcbnew
from board.wiring import common
from components.sk9822 import Sk9822, Sk9822Pin


def route_led_chain(
    board, net_by_name, pads, connections, *, obstructed_only=False
) -> None:
    """Route regular links first and expander-obstructed links after sensors."""
    origin = pcbnew.FromMM(kicad.ORIGIN_X_MM)
    for connection in connections.connections:
        nodes = list(connection.endpoints)
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
        name = connection.name
        net = net_by_name[name]
        start, end = (pads[node].GetPosition() for node in nodes)
        c0, c1 = (pads[node].GetParent().GetPosition() for node in nodes)
        if c0.y == c1.y:
            # Four links per half-board pass the quadrant expanders. Drop those
            # links to the free bottom layer and take a lane between sensor rows.
            x0, x1 = sorted((start.x, end.x))
            blocker = next(
                (
                    module.GetBoundingBox()
                    for module in board.GetFootprints()
                    if module.GetReference() not in {nodes[0][0], nodes[1][0]}
                    and module.GetBoundingBox().GetLeft() <= x1
                    and module.GetBoundingBox().GetRight() >= x0
                    and module.GetBoundingBox().GetTop()
                    <= start.y
                    <= module.GetBoundingBox().GetBottom()
                ),
                None,
            )
            if blocker is None:
                if not obstructed_only:
                    kicad.add_trace(board, net, start, end)
                continue
            if obstructed_only:
                route = common.find_route(
                    board,
                    net,
                    start,
                    end,
                    preferred_layer_index=0,
                    required_end_layer_index=0,
                )
                grid_router.apply_route(board, net, start, end, route)
            continue

        if obstructed_only:
            continue
        # Rank transitions run at the board edge. Clock remains on top; data
        # changes to the bottom so the two transitions cannot cross each other.
        right_side = start.x > origin
        direction = 1 if right_side else -1
        is_clock = nodes[0][1] == Sk9822Pin.CLOCK_OUT
        distance_mm = (
            (3.0 if right_side else 8.0) if is_clock else (1.0 if right_side else 6.0)
        )
        distance = pcbnew.FromMM(distance_mm)
        first = pcbnew.VECTOR2I(start.x + direction * distance, start.y)
        second = pcbnew.VECTOR2I(end.x + direction * distance, end.y)
        if is_clock:
            kicad.add_trace(board, net, start, first)
            kicad.add_trace(board, net, first, second)
            kicad.add_trace(board, net, second, end)
        else:
            kicad.add_trace(board, net, start, first)
            kicad.add_trace(board, net, second, end)
            kicad.add_via(board, net, first)
            kicad.add_via(board, net, second)
            kicad.add_trace(board, net, first, second, pcbnew.B_Cu)
