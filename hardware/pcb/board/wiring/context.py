"""Shared native routing state and the small interface implemented by each stage."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Unpack

from base.connectivity import Connection, ConnectionGraph, EndpointKey
from base.design import BoardDesign
from base.kicad import grid_router
from base.kicad.api import pcbnew
from base.kicad.board import KiCadBoard
from board.wiring import common


@dataclass(frozen=True)
class WiringContext:
    """Borrow one layout's native objects; never copy or redefine its net graph.

    The context is immutable, but its board is deliberately mutable. Stages share
    copper as it is added, so later searches see earlier routes as obstacles.
    ``design`` is only needed for the Hall-bank placement contract.
    """

    board: pcbnew.BOARD
    nets: Mapping[str, pcbnew.NETINFO_ITEM]
    pads: Mapping[EndpointKey, pcbnew.PAD]
    connections: ConnectionGraph | None = None
    design: BoardDesign | None = None

    @classmethod
    def from_layout(cls, layout: KiCadBoard) -> WiringContext:
        return cls(
            layout.native, layout.nets, layout.pads, layout.connections, layout.design
        )

    @property
    def graph(self) -> ConnectionGraph:
        if self.connections is None:
            raise ValueError("this wiring stage requires a connection graph")
        return self.connections

    def connection(self, name: str) -> Connection:
        return self.graph.named(name)


class WiringStage(ABC):
    """A copper-producing stage with shared endpoint escape and path application.

    Subclasses implement routing policy, not another electrical net definition.
    Pure coordinate helpers stay functions rather than static-method namespaces.
    """

    def __init__(self, context: WiringContext) -> None:
        self.context = context

    @abstractmethod
    def route(self) -> None:
        """Add this stage's copper to the shared board."""

    def escape(
        self, name: str, endpoint: EndpointKey, *, add_via: bool = False
    ) -> pcbnew.VECTOR2I:
        return common.signal_escape(
            self.context.board,
            self.context.nets[name],
            self.context.pads[endpoint],
            add_via=add_via,
        )

    def connect(
        self,
        net: pcbnew.NETINFO_ITEM,
        start: pcbnew.VECTOR2I,
        end: pcbnew.VECTOR2I,
        **options: Unpack[grid_router.RoutingOptions],
    ) -> None:
        """Search and apply a route with the common chess-board keepouts."""
        route = common.find_route(self.context.board, net, start, end, **options)
        grid_router.apply_route(self.context.board, net, start, end, route)
