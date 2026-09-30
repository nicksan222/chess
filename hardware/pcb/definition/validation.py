"""Physical, product, and logical-connectivity checks for the native board."""

from collections import Counter

import pcbnew

from pcb.definition.assemblies import controls, power, sensing, square
from pcb.definition.bank_assemblies import BANK_ASSEMBLIES
from pcb.definition.native import connections, endpoint_pads, logical_pin, parts, point
from pcb.definition.parts.catalog import PCB_PARTS
from shared import dimensions, wiring
from shared.components import COMPONENTS
from shared.electronics import Endpoint
from shared.electronics.hall_sensor import HallSensorPin


def validate(board: pcbnew.BOARD) -> None:
    from pcb.definition import rules
    from shared.electronics.tca9554 import Tca9554Component, Tca9554Pin

    rules.validate()
    footprints = parts(board)
    graph = connections(board)
    actual = Counter(f.GetFieldText("Assembly") for f in footprints)
    expected = {
        "power": power.ASSEMBLY_PART_COUNT,
        "controls": controls.ASSEMBLY_PART_COUNT,
        **{
            f"square/{board_square.name}": square.ASSEMBLY_PART_COUNT
            for board_square in dimensions.BOARD_SQUARES
        },
        **{
            bank_assembly.assembly_name: sensing.ASSEMBLY_PART_COUNT
            for bank_assembly in BANK_ASSEMBLIES
        },
    }
    for name, count in expected.items():
        if actual[name] != count:
            raise ValueError(
                f"{name}: expected {count} components, found {actual[name]}"
            )
    if unexpected := actual.keys() - expected.keys():
        raise ValueError(f"unexpected assemblies: {sorted(unexpected)}")
    for footprint in footprints:
        ref = footprint.GetReference()
        key = footprint.GetFieldText("PartKey")
        spec = COMPONENTS[key]
        model = PCB_PARTS[key].new_model(ref)
        if (
            footprint.GetValue() != spec.mpn
            or footprint.GetFieldText("Package") != spec.package
        ):
            raise ValueError(f"{ref}: unapproved product/package")
        physical = {logical_pin(p) for p in footprint.Pads()}
        if physical != {p.endpoint.pin for p in model.pins} or any(
            p.GetNetCode() == 0 for p in footprint.Pads()
        ):
            raise ValueError(f"{ref}: incomplete physical/logical pin assignment")
    if any(
        name.startswith("unconnected-") and len(nodes) != 1
        for name, nodes in graph.items()
    ):
        raise ValueError("no-connect nets must contain one logical pin")
    pads = endpoint_pads(board)
    for bank_assembly in BANK_ASSEMBLIES:
        bank = bank_assembly.bank
        ref = bank_assembly.expander_reference
        expected = {
            Tca9554Pin.SUPPLY: "+3V3",
            Tca9554Pin.GROUND: "GND",
            Tca9554Pin.I2C_CLOCK: wiring.SCL_NET,
            Tca9554Pin.I2C_DATA: wiring.SDA_NET,
            Tca9554Pin.INTERRUPT: f"unconnected-({ref}-Pad13)",
        }
        expected.update(
            zip(
                (Tca9554Pin.ADDRESS_0, Tca9554Pin.ADDRESS_1, Tca9554Pin.ADDRESS_2),
                ("+3V3" if high else "GND" for high in bank.straps),
                strict=True,
            )
        )
        for pin, name in expected.items():
            if pads[Endpoint(ref, pin)].GetNetname() != name:
                raise ValueError(f"{ref}: incorrect {pin.name} assignment")
        for pin, member in zip(
            Tca9554Component.input_pins(), bank.members, strict=True
        ):
            name = wiring.sense_net(member.name)
            if set(graph[name]) != {
                Endpoint(ref, pin),
                Endpoint(
                    f"HS{dimensions.BOARD_SQUARES.by_position(member).sensor_number}",
                    HallSensorPin.ACTIVE_LOW_OUTPUT,
                ),
            }:
                raise ValueError(f"{bank.label}: incorrect Hall mapping")
    for board_square in dimensions.BOARD_SQUARES:
        name = board_square.name
        members = [
            f for f in footprints if f.GetFieldText("Assembly") == f"square/{name}"
        ]
        if sorted(f.GetFieldText("PartKey") for f in members) != [
            "CAP_100N",
            "CAP_100N",
            "HALL_SENSOR",
            "SK9822",
        ]:
            raise ValueError(f"{name}: incomplete square assembly")
        sensor = next(f for f in members if f.GetFieldText("PartKey") == "HALL_SENSOR")
        if sensor.GetPosition() != point(*board_square.hall_position_mm):
            raise ValueError(f"{name}: sensor is not at the shared square centre")
