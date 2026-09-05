"""Shared routing behaviour for multi-drop host signals and internal buses."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Unpack

from board.wiring import common
from board.wiring.context import WiringStage
from domain.component import ComponentReference
from domain.connectivity import Connection, EndpointKey
from kicad.api import pcbnew
from kicad.grid_router import RoutingOptions


class SignalTreeWiring(WiringStage):
    """Share host-first ordering, SMD escapes, and deterministic tree construction.

    Concrete stages choose *when* to reserve escapes and which layers to use.
    Those scheduling differences are important in the crowded header bay.
    """

    def nodes(self, connection: Connection) -> list[EndpointKey]:
        return sorted(
            connection.endpoints,
            key=lambda node: (
                node[0] != ComponentReference.HOST_GPIO_HEADER,
                node[0],
                node[1],
            ),
        )

    def reserve(
        self, connection: Connection, nodes: Sequence[EndpointKey]
    ) -> dict[EndpointKey, pcbnew.VECTOR2I]:
        return {
            node: self.escape(connection.name, node, add_via=True) for node in nodes
        }

    def route_tree(
        self,
        connection: Connection,
        nodes: Sequence[EndpointKey],
        route_points: Mapping[EndpointKey, pcbnew.VECTOR2I],
        *,
        label_errors: bool = False,
        **options: Unpack[RoutingOptions],
    ) -> None:
        net = self.context.nets[connection.name]
        for left, right in common.nearest_tree_edges(nodes, route_points):
            try:
                self.connect(net, route_points[left], route_points[right], **options)
            except RuntimeError as error:
                if label_errors:
                    raise RuntimeError(f"{error}: {left} -> {right}") from error
                raise
