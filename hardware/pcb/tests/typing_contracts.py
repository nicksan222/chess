"""Positive static regressions included in the PCB Pyright gate, not unit discovery."""

from typing import assert_type

from base.component import ComponentPin, Endpoint
from base.connectivity import CircuitBuilder, Connection, ConnectionGraph
from base.kicad.api import pcbnew
from base.kicad.board import KiCadBoard
from base.kicad.grid_router import RoutingOptions
from board.wiring.context import WiringContext
from board.wiring.controls import ControlSignalWiring
from board.wiring.nets import Net
from components.hall_sensor import HallSensor, HallSensorPin
from components.tca9554 import Tca9554, Tca9554Pin


def typed_connections() -> None:
    hall = HallSensor("HS1")
    expander = Tca9554("U1")
    pin = hall.pin(HallSensorPin.ACTIVE_LOW_OUTPUT)
    assert_type(pin, ComponentPin[HallSensorPin])
    assert_type(pin.endpoint, Endpoint[HallSensorPin])
    assert_type(hall.resolve_endpoint("2"), Endpoint[HallSensorPin])
    # A graph accepts heterogeneous bound pins without erasing their enum types.
    connection = Connection.from_pins("SQ_A1", pin, expander.pin(Tca9554Pin.P0))
    assert_type(connection, Connection)
    assert_type(CircuitBuilder().add(connection).build(), ConnectionGraph)


def typed_native_wiring(layout: KiCadBoard) -> None:
    context = WiringContext.from_layout(layout)
    assert_type(context.connection(Net.GROUND), Connection)
    assert_type(context.nets[Net.GROUND], pcbnew.NETINFO_ITEM)
    assert_type(context.pads[("HS1", "2")], pcbnew.PAD)
    policy: RoutingOptions = {"allow_vias": False, "layers": (pcbnew.B_Cu,)}
    wiring = ControlSignalWiring(context)
    at = pcbnew.VECTOR2I(0, 0)
    wiring.connect(context.nets[Net.GROUND], at, at, **policy)
    if context.design is not None:
        model = context.design.component("U1").model_as(Tca9554)
        assert_type(model, Tca9554)
        assert_type(model.pin(Tca9554Pin.P0), ComponentPin[Tca9554Pin])
