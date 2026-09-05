"""Compose subsystem wiring objects in their copper-dependency order."""

from __future__ import annotations

from base.kicad import board as kicad
from board.wiring import common
from board.wiring.buttons import ButtonWiring
from board.wiring.context import WiringContext, WiringStage
from board.wiring.controls import ControlSignalWiring, InternalBusWiring
from board.wiring.led import LedChainWiring
from board.wiring.power import InputPowerWiring, PowerFanoutWiring
from board.wiring.sensors import HallSensorWiring


class ChessBoardRouter:
    """Own a composed pipeline; subsystem objects own the actual routing policies."""

    def __init__(self, layout: kicad.KiCadBoard) -> None:
        self.layout = layout
        self.context = WiringContext.from_layout(layout)
        self.sensors = HallSensorWiring(self.context)
        self.before_sensor_reservation: tuple[WiringStage, ...] = (
            PowerFanoutWiring(self.context),
            LedChainWiring(self.context),
            ControlSignalWiring(self.context),
        )
        self.after_sensor_reservation: tuple[WiringStage, ...] = (
            ButtonWiring(self.context),
            InternalBusWiring(self.context),
            self.sensors,
            LedChainWiring(self.context, obstructed_only=True),
            InputPowerWiring(self.context),
        )

    def route(self) -> None:
        for stage in self.before_sensor_reservation:
            stage.route()
        # Hall escapes must exist before buses are searched, but their full paths
        # are deliberately deferred until buttons and I2C have claimed lanes.
        self.sensors.reserve()
        for stage in self.after_sensor_reservation:
            stage.route()
        common.prune_unused_signal_vias(self.context.board)
