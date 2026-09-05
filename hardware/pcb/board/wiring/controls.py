"""Host control signals and shared buses specialize the same tree wiring policy."""

from __future__ import annotations

from collections.abc import Mapping

from board.wiring import common
from board.wiring.buttons import route_buttons
from board.wiring.context import WiringContext
from board.wiring.nets import Net
from board.wiring.signal_tree import SignalTreeWiring
from domain.connectivity import ConnectionGraph, EndpointKey
from kicad.api import pcbnew

__all__ = [
    "ControlSignalWiring",
    "InternalBusWiring",
    "route_buttons",
    "route_control_signals",
    "route_internal_buses",
]


class ControlSignalWiring(SignalTreeWiring):
    """Reserve all SPI/LED input escapes before routing any of their trees."""

    def route(self) -> None:
        selected = sorted(
            (
                connection
                for connection in self.context.graph.connections
                if connection.name in common.CONTROL_SIGNAL_NETS
            ),
            key=lambda connection: connection.name,
        )
        reserved_points = {
            connection.name: self.reserve(connection, connection.endpoints)
            for connection in selected
        }
        for connection in selected:
            self.route_tree(
                connection,
                self.nodes(connection),
                reserved_points[connection.name],
                allow_vias=True,
                label_errors=True,
            )


class InternalBusWiring(SignalTreeWiring):
    """Route each I2C bus after reserving its host-first ordered escapes."""

    def route(self) -> None:
        for layer_index, name in enumerate((Net.I2C_SDA, Net.I2C_SCL)):
            connection = self.context.connection(name)
            nodes = self.nodes(connection)
            self.route_tree(
                connection,
                nodes,
                self.reserve(connection, nodes),
                preferred_layer_index=layer_index,
                allow_vias=True,
                layers=common.INTERNAL_SIGNAL_LAYERS,
            )


def route_control_signals(
    board: pcbnew.BOARD,
    net_by_name: Mapping[str, pcbnew.NETINFO_ITEM],
    pads: Mapping[EndpointKey, pcbnew.PAD],
    graph: ConnectionGraph,
) -> None:
    """Compatibility entry point for callers supplying native routing objects."""
    ControlSignalWiring(WiringContext(board, net_by_name, pads, graph)).route()


def route_internal_buses(
    board: pcbnew.BOARD,
    net_by_name: Mapping[str, pcbnew.NETINFO_ITEM],
    pads: Mapping[EndpointKey, pcbnew.PAD],
    graph: ConnectionGraph,
) -> None:
    """Compatibility entry point; pipelines compose ``InternalBusWiring``."""
    InternalBusWiring(WiringContext(board, net_by_name, pads, graph)).route()
