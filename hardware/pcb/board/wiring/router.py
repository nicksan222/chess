"""Ordered object-oriented routing pipeline for the complete board."""

from __future__ import annotations

from base.kicad import board as kicad
from board.wiring import common, controls, led, power, sensors


class ChessBoardRouter:
    """Run focused native-KiCad routers in their required dependency order."""

    def __init__(self, layout: kicad.KiCadBoard) -> None:
        self.layout = layout

    def route(self) -> None:
        board = self.layout.native
        nets = self.layout.nets
        pads = self.layout.pads
        connections = self.layout.connections

        power.fanout_power(board, nets)
        led.route_led_chain(board, nets, pads, connections)
        controls.route_control_signals(board, nets, pads, connections)
        square_routes = sensors.reserve_square_sensor_breakouts(
            board, nets, pads, connections
        )
        controls.route_buttons(board, nets, pads, connections)
        controls.route_internal_buses(board, nets, pads, connections)
        sensors.route_square_sensors(board, square_routes)
        led.route_led_chain(board, nets, pads, connections, obstructed_only=True)
        power.route_input_power(board, nets, pads)
        common.prune_unused_signal_vias(board)
