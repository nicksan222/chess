"""Native KiCad routing for repeated Hall-sensor outputs."""

from __future__ import annotations

from core import grid_router, sources
from core import routing_common as common


def reserve_square_sensor_breakouts(board, net_by_name, pads):
    """Reserve every Hall/expander escape and via before shared-bus routing."""
    pending = []
    for connection in sources.netlist()["connections"]:
        name = connection["name"]
        if not name or not name.startswith("SQ_"):
            continue
        nodes = [tuple(node) for node in connection["pads"]]
        if len(nodes) != 2:
            raise RuntimeError(f"{name}: square sensor net must have two pads")
        net = net_by_name[name]
        points = tuple(
            common.signal_escape(board, net, pads[node], add_via=True) for node in nodes
        )
        pending.append((net, *points))
    return pending


def route_square_sensors(board, pending) -> None:
    """Route reserved Hall outputs without crossing buses or power fanouts."""
    for net, start, end in pending:
        route = grid_router.find_route(
            board,
            net,
            start,
            end,
            layers=common.SENSOR_ROUTING_LAYERS,
            diagonals=True,
        )
        grid_router.apply_route(board, net, start, end, route)
