"""The four-part square: explicit membership, local wiring, and placement."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from itertools import pairwise

import pcbnew

from pcb.definition.assemblies import led_link_names
from pcb.definition.native import connect, no_connect, place
from pcb.definition.parts import catalog as parts
from shared import dimensions, wiring
from shared.electronics import CapacitorPin, HallSensorPin, Sk9822Pin
from shared.electronics import HallSensorComponent as HallSensor
from shared.electronics import Sk9822Component as Sk9822
from shared.squares import BoardSquare

ASSEMBLY_PART_COUNT = 4


@dataclass(frozen=True)
class Square:
    name: str
    led: Sk9822
    hall_sensor: HallSensor


LED_BYPASS_OFFSET_MM = (0.0, -8.0)
HALL_BYPASS_OFFSET_MM = (0.0, -3.0)


def add_square(board: pcbnew.BOARD, *, board_square: BoardSquare) -> Square:
    name = board_square.name
    rank = board_square.position.rank
    chain_index = board_square.led_chain_index
    sensor_index = board_square.sensor_number - 1
    x, y = board_square.hall_position_mm
    lx, ly = board_square.led_position_mm
    assembly = f"square/{name}"
    led = place(
        board,
        parts.SK9822_PART,
        f"U{6 + chain_index}",
        at=(lx, ly),
        rotation=180 if (rank + 1) % 2 == 0 else 0,
        assembly=assembly,
        extras={"Square": name, "ChainIndex": str(chain_index + 1)},
    )
    sensor = place(
        board,
        parts.HALL_SENSOR_PART,
        f"HS{1 + sensor_index}",
        at=(x, y),
        assembly=assembly,
        extras={"Square": name},
    )
    led_cap = place(
        board,
        parts.CAP_100N_PART,
        f"C{8 + chain_index}",
        at=(
            lx + LED_BYPASS_OFFSET_MM[0],
            ly + LED_BYPASS_OFFSET_MM[1],
        ),
        assembly=assembly,
        purpose="Local LED decoupling capacitor",
        extras={"Square": name},
    )
    sensor_cap = place(
        board,
        parts.CAP_100N_PART,
        f"C{72 + sensor_index}",
        at=(
            x + HALL_BYPASS_OFFSET_MM[0],
            y + HALL_BYPASS_OFFSET_MM[1],
        ),
        assembly=assembly,
        purpose="Local Hall-sensor decoupling capacitor",
        extras={"Square": name, "Sensor": sensor.reference},
    )
    connect(
        board,
        "+5V",
        led.pin(Sk9822Pin.FIVE_VOLTS),
        led_cap.pin(CapacitorPin.SUPPLY_OR_ELECTRODE_A),
    )
    connect(
        board,
        "+3V3",
        sensor.pin(HallSensorPin.SUPPLY),
        sensor_cap.pin(CapacitorPin.SUPPLY_OR_ELECTRODE_A),
    )
    connect(
        board,
        "GND",
        led.pin(Sk9822Pin.GROUND),
        sensor.pin(HallSensorPin.GROUND),
        led_cap.pin(CapacitorPin.RETURN_OR_ELECTRODE_B),
        sensor_cap.pin(CapacitorPin.RETURN_OR_ELECTRODE_B),
    )
    return Square(name, led, sensor)


def connect_led_chain(board: pcbnew.BOARD, squares: Mapping[str, Square]) -> None:
    chain = [squares[square.name].led for square in dimensions.BOARD_SQUARES.led_chain]
    connect(board, wiring.LED_DATA_NET, chain[0].pin(Sk9822Pin.DATA_IN))
    connect(board, wiring.LED_CLOCK_NET, chain[0].pin(Sk9822Pin.CLOCK_IN))
    for left_square, right_square in pairwise(dimensions.BOARD_SQUARES.led_chain):
        left = squares[left_square.name].led
        right = squares[right_square.name].led
        data, clock = led_link_names.for_squares(
            left_square.position, right_square.position
        )
        connect(board, data, left.pin(Sk9822Pin.DATA_OUT), right.pin(Sk9822Pin.DATA_IN))
        connect(
            board, clock, left.pin(Sk9822Pin.CLOCK_OUT), right.pin(Sk9822Pin.CLOCK_IN)
        )
    no_connect(board, chain[-1].pin(Sk9822Pin.DATA_OUT))
    no_connect(board, chain[-1].pin(Sk9822Pin.CLOCK_OUT))
