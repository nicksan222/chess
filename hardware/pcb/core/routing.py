"""Ordered object-oriented routing pipeline for the complete board."""

from __future__ import annotations

from core import (
    kicad,
    routing_common,
    routing_controls,
    routing_led,
    routing_power,
    routing_sensors,
)


class ChessBoardRouter:
    """Run focused native-KiCad routers in their required dependency order."""

    def __init__(self, layout: kicad.KiCadBoard) -> None:
        self.layout = layout

    def route(self) -> None:
        board = self.layout.native
        nets = self.layout.nets
        pads = self.layout.pads

        routing_power.fanout_power(board, nets)
        routing_led.route_led_chain(board, nets, pads)
        routing_controls.route_control_signals(board, nets, pads)
        square_routes = routing_sensors.reserve_square_sensor_breakouts(
            board, nets, pads
        )
        routing_controls.route_buttons(board, nets, pads)
        routing_controls.route_internal_buses(board, nets, pads)
        routing_sensors.route_square_sensors(board, square_routes)
        routing_led.route_led_chain(board, nets, pads, obstructed_only=True)
        routing_power.route_input_power(board, nets, pads)
        routing_common.prune_unused_signal_vias(board)
