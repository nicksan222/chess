"""Bind shared Hall-bank geometry to the reviewed electrical graph."""

from collections.abc import Iterator

from base.design import BoardDesign, ComponentInstance
from components.hall_sensor import HallSensor, HallSensorPin
from components.tca9554 import Tca9554, Tca9554Pin
from shared.dimensions import HALL_BANKS
from shared.hall_banks import HallBank, square
from shared.wiring import SCL_NET, SDA_NET, sense_net


def instances(design: BoardDesign) -> Iterator[tuple[HallBank, ComponentInstance]]:
    """Yield banks in address order, rejecting missing or duplicate ownership."""
    expanders = [c for c in design.components.values() if isinstance(c.model, Tca9554)]
    if len(expanders) != len(HALL_BANKS):
        raise ValueError("board requires eight Hall banks")
    for bank in HALL_BANKS:
        matches = [c for c in expanders if c.spec.extras.get("Bank") == bank.label]
        if len(matches) != 1:
            raise ValueError(f"{bank.label}: expected one expander")
        yield bank, matches[0]


def validate(design: BoardDesign) -> None:
    """Fail generation when reviewed connectivity disagrees with bank ownership."""
    graph = design.connections
    for bank, component in instances(design):
        model = component.model
        if component.spec.extras.get("Address") != f"0x{bank.address:02X}":
            raise ValueError(f"{bank.label}: address metadata disagrees with bank")
        required = {
            Tca9554Pin.SUPPLY: "+3V3",
            Tca9554Pin.GROUND: "GND",
            Tca9554Pin.I2C_CLOCK: SCL_NET,
            Tca9554Pin.I2C_DATA: SDA_NET,
        }
        required.update(
            zip(
                (Tca9554Pin.ADDRESS_0, Tca9554Pin.ADDRESS_1, Tca9554Pin.ADDRESS_2),
                ("+3V3" if high else "GND" for high in bank.straps),
                strict=True,
            )
        )
        for pin, net in required.items():
            if model.pin(pin).net_name(graph) != net:
                raise ValueError(f"{bank.label}: incorrect {pin.name} connection")
        if not graph.connection_for(model.endpoint(Tca9554Pin.INTERRUPT)).no_connect:
            raise ValueError(f"{bank.label}: polled INT must be explicitly NC")
        for pin, member in zip(Tca9554.input_pins(), bank.members, strict=True):
            name = square(*member)
            connection = graph.connection_for(model.endpoint(pin))
            peers = model.pin(pin).peers(graph)
            if connection.name != sense_net(name) or len(peers) != 1:
                raise ValueError(f"{bank.label}: incorrect Hall mapping for {name}")
            sensor = design.component(peers[0].reference)
            if (
                not isinstance(sensor.model, HallSensor)
                or sensor.spec.extras.get("Square") != name
                or peers[0] != sensor.model.endpoint(HallSensorPin.ACTIVE_LOW_OUTPUT)
            ):
                raise ValueError(
                    f"{bank.label}: {name} is not attached to its Hall sensor output"
                )
