"""Read this first: native KiCad board construction from typed subsystem ports."""

from __future__ import annotations

import pcbnew

from pcb.definition.native import (
    add_mechanical_features,
    connections,
    endpoint_pads,
    logical_pin,
    new_board,
    parts,
    point,
)
from pcb.definition.parts.catalog import MODELS
from shared import dimensions, wiring
from shared.components import COMPONENTS
from shared.electronics.hall_sensor import HallSensorPin
from shared.hall_banks import square as square_name


def square_centres() -> dict[str, tuple[float, float]]:
    return {
        f"{wiring.FILES[column]}{dimensions.GRID_COUNT - row}": (x, y)
        for row, column, x, y in dimensions.BOARD_SQUARE_CENTERS_MM
    }


def load() -> pcbnew.BOARD:
    from pcb.definition.assemblies import controls, power, sensing, square

    board = new_board()
    power.add_power(board)
    controls.add_controls(board)
    squares = {
        name: square.add_square(board, name=name, at=at)
        for name, at in square_centres().items()
    }
    sensing.add_sensor_banks(board, squares=squares)
    square.connect_led_chain(board, squares)
    add_mechanical_features(board)
    validate(board)
    return board


def validate(board: pcbnew.BOARD) -> None:
    from pcb.definition import rules
    from pcb.definition.assemblies import sensing, square
    from shared.electronics.tca9554 import Tca9554Component, Tca9554Pin

    rules.validate()
    footprints = parts(board)
    graph = connections(board)
    if len(footprints) != 303 or len(graph) != 237:
        raise ValueError("D-PROTOTYPE requires 303 components and 237 connections")
    for footprint in footprints:
        ref = footprint.GetReference()
        key = footprint.GetFieldText("PartKey")
        spec = COMPONENTS[key]
        model = MODELS[key](ref)
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
    for bank, (ref, _) in zip(
        dimensions.HALL_BANKS, sensing.BANK_REFERENCES, strict=True
    ):
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
            if pads[ref, pin].GetNetname() != name:
                raise ValueError(f"{ref}: incorrect {pin.name} assignment")
        for pin, member in zip(
            Tca9554Component.input_pins(), bank.members, strict=True
        ):
            name = wiring.sense_net(square_name(*member))
            if set(graph[name]) != {
                (ref, str(pin)),
                (f"HS{square.sensor_number(*member)}", HallSensorPin.ACTIVE_LOW_OUTPUT),
            }:
                raise ValueError(f"{bank.label}: incorrect Hall mapping")
    for name, at in square_centres().items():
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
        if sensor.GetPosition() != point(*at):
            raise ValueError(f"{name}: sensor is not at the shared square centre")


def netlist(board: pcbnew.BOARD | None = None) -> dict[str, object]:
    """Expanded output derived from native fields and actual pad-to-net assignment."""
    board = board if board is not None else load()
    graph = connections(board)
    return {
        "title": board.GetTitleBlock().GetTitle(),
        "revision": board.GetTitleBlock().GetRevision(),
        "components": {
            f.GetReference(): {
                "part_key": f.GetFieldText("PartKey"),
                "package": f.GetFieldText("Package"),
                "lib": f.GetFieldText("Library"),
                "value": f.GetFieldText("NominalValue"),
                "description": f.GetFieldText("Purpose"),
                "assembly": f.GetFieldText("Assembly"),
                "extras": {
                    k: v
                    for k, v in f.GetFieldsText().items()
                    if k
                    in (
                        "Square",
                        "ChainIndex",
                        "Sensor",
                        "Bank",
                        "Address",
                        "For",
                        "Function",
                    )
                },
            }
            for f in parts(board)
        },
        "connections": [
            {
                "name": name,
                "pads": [list(e) for e in nodes],
                **({"no_connect": True} if name.startswith("unconnected-") else {}),
            }
            for name, nodes in graph.items()
        ],
        "nets": {
            name: [list(e) for e in nodes]
            for name, nodes in graph.items()
            if not name.startswith("unconnected-")
        },
    }
