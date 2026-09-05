"""Native KiCad routing for compact Hall banks, confined to their own rectangles."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

from base.connectivity import EndpointKey
from base.design import BoardDesign
from base.kicad import board as kicad
from base.kicad.api import pcbnew
from board import hall_banks
from board.wiring import common
from board.wiring.context import WiringContext, WiringStage
from components.tca9554 import Tca9554
from shared.dimensions import PLAYING_SPAN_MM, SQUARE_SIZE_MM
from shared.hall_banks import BANK_FILES, BANK_RANKS, HallBank

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
    top_left = kicad.point(cx - half_x, cy + half_y)
    bottom_right = kicad.point(cx + half_x, cy - half_y)
    return (
        pcbnew.ToMM(top_left.x),
        pcbnew.ToMM(top_left.y),
        pcbnew.ToMM(bottom_right.x),
        pcbnew.ToMM(bottom_right.y),
    )


class HallSensorWiring(WiringStage):
    """Own Hall escape reservations across the intervening shared-bus stages."""

    def __init__(self, context: WiringContext) -> None:
        super().__init__(context)
        self.pending: list[PendingHallRoute] = []

    def reserve(self) -> list[PendingHallRoute]:
        """Reserve bank/address/port escapes before shared buses add obstacles."""
        design = self.context.design
        if design is None:
            raise ValueError("Hall reservations require a board design")
        net_by_name = self.context.nets
        self.pending = []
        for bank, component in hall_banks.instances(design):
            model = component.model_as(Tca9554)
            bounds = _bank_routing_bounds_mm(bank)
            for pin in Tca9554.input_pins():
                connection = design.connections.connection_for(model.endpoint(pin))
                net = net_by_name[connection.name]
                start, end = (
                    self.escape(connection.name, node, add_via=True)
                    for node in connection.endpoints
                )
                self.pending.append(PendingHallRoute(net, start, end, bounds))
        return self.pending

    def route(self) -> None:
        """Keep every reserved signal inside its own bank, never its neighbour."""
        for pending_route in self.pending:
            self.connect(
                pending_route.net,
                pending_route.start,
                pending_route.end,
                layers=common.SENSOR_ROUTING_LAYERS,
                diagonals=True,
                routing_bounds_mm=pending_route.bounds_mm,
            )


def reserve_square_sensor_breakouts(
    board: pcbnew.BOARD,
    net_by_name: Mapping[str, pcbnew.NETINFO_ITEM],
    pads: Mapping[EndpointKey, pcbnew.PAD],
    design: BoardDesign,
) -> list[PendingHallRoute]:
    """Compatibility entry point for callers that retain the pending list."""
    return HallSensorWiring(
        WiringContext(board, net_by_name, pads, design.connections, design)
    ).reserve()


def route_square_sensors(board: pcbnew.BOARD, pending: list[PendingHallRoute]) -> None:
    """Compatibility entry point; new pipelines keep a ``HallSensorWiring``."""
    wiring = HallSensorWiring(WiringContext(board, {}, {}))
    wiring.pending = pending
    wiring.route()
