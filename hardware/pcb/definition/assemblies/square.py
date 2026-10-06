"""The four-part square: explicit membership, local wiring, and placement.

Role: each of the 64 squares is a repeated assembly of an SK9822-A LED, a DRV5032 Hall sensor
and a decoupling capacitor for each, placed from the shared square layout. This module also
links the LEDs into their daisy chain. Reference numbering is fixed by the chain index and
sensor number so published designators never depend on build order.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from itertools import pairwise

import pcbnew

from pcb.definition import native
from pcb.definition.assemblies import led_link_names
from pcb.definition.native import connect, no_connect, place
from pcb.definition.parts import catalog as parts
from shared import dimensions, wiring
from shared.electronics import CapacitorPin, HallSensorPin, ResistorPin, Sk9822Pin
from shared.electronics import HallSensorComponent as HallSensor
from shared.electronics import ResistorComponent as Resistor
from shared.electronics import Sk9822Component as Sk9822
from shared.squares import BoardSquare

ASSEMBLY_PART_COUNT = 4


@dataclass(frozen=True)
class Square:
    """Handles to the parts of one placed square (its LED and Hall sensor), so later steps
    wire them by reference without searching footprints.
    """

    name: str
    led: Sk9822
    hall_sensor: HallSensor


# Bypass capacitors sit on the supply-pin side within 3 mm edge to edge (see
# tests/board/test_decoupling.py). For an unrotated LED, VCC/GND (pins 4/3) are
# the +Y row, so the capacitor turns with the LED and stays clear of its rail vias.
LED_BYPASS_OFFSET_MM = (0.0, 4.0)
HALL_BYPASS_OFFSET_MM = (0.0, -2.4)
# S5 (lead-approved): the left rank-turn data hops leave F.Cu for In4 (about 56
# ohm), which rings with a strong SK9822 output; a 56 ohm source termination sits
# in the F.Cu stub between the driving LED's DO pad and the In4 via. Keyed by the
# driving square.
LED_TURN_TERMINATIONS: Mapping[str, str] = {"A2": "R10", "A4": "R11", "A6": "R12"}
LED_CHAIN_ASSEMBLY = "led-chain"
# Placement of each terminator along the F.Cu stub, outward from the DO pad (mm).
LED_TURN_TERMINATION_OFFSET_MM = 3.05  # DO pad centre to resistor centre, outward.


def add_square(board: pcbnew.BOARD, *, board_square: BoardSquare) -> Square:
    """Place the four parts of one square and wire its local nets.

    LED (U6+chain index), Hall sensor (HS<sensor number>) and a 100 nF capacitor for each. The
    LED is rotated so its output pins face the next LED in the serpentine, which alternates by
    rank. Local nets: LED_5V and GND for the LED, +3V3 and GND for the sensor. Chain and sense
    nets are connected later (`connect_led_chain`, `sensing.add_sensor_banks`).
    """
    name = board_square.name
    rank = board_square.position.rank
    chain_index = board_square.led_chain_index
    sensor_index = board_square.sensor_number - 1
    x, y = board_square.hall_position_mm
    lx, ly = board_square.led_position_mm
    assembly = f"square/{name}"
    # Inputs sit on the package's +X side, so face outputs downstream.
    led_rotation = 0 if rank % 2 else 180
    led_side = 1 if led_rotation == 0 else -1
    led = place(
        board,
        parts.SK9822_PART,
        f"U{6 + chain_index}",
        at=(lx, ly),
        rotation=led_rotation,
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
            lx + led_side * LED_BYPASS_OFFSET_MM[0],
            ly + led_side * LED_BYPASS_OFFSET_MM[1],
        ),
        rotation=led_rotation,
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
    # S6: the LEDs run from the switched LED_5V rail (In6 plane, Q1).
    connect(
        board,
        wiring.LED_SUPPLY_NET,
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
    """Daisy-chain the 64 LEDs in serpentine order and mark the last outputs unused.

    The first LED's inputs join the buffered LED data/clock nets. Each hop gets its published
    net name (`led_link_names`); at the three left rank turns a 56 ohm terminator splits the data
    hop into `<name>_SRC` and `<name>`. The last LED's outputs are explicit no-connects.
    """
    chain = [squares[square.name].led for square in dimensions.BOARD_SQUARES.led_chain]
    connect(board, wiring.LED_DATA_NET, chain[0].pin(Sk9822Pin.DATA_IN))
    connect(board, wiring.LED_CLOCK_NET, chain[0].pin(Sk9822Pin.CLOCK_IN))
    for left_square, right_square in pairwise(dimensions.BOARD_SQUARES.led_chain):
        left = squares[left_square.name].led
        right = squares[right_square.name].led
        data, clock = led_link_names.for_squares(
            left_square.position, right_square.position
        )
        terminator = LED_TURN_TERMINATIONS.get(left_square.name)
        if terminator is None:
            connect(
                board, data, left.pin(Sk9822Pin.DATA_OUT), right.pin(Sk9822Pin.DATA_IN)
            )
        else:
            resistor = _turn_termination(board, left, terminator)
            connect(
                board,
                f"{data}_SRC",
                left.pin(Sk9822Pin.DATA_OUT),
                resistor.pin(ResistorPin.TERMINAL_B),
            )
            connect(
                board,
                data,
                resistor.pin(ResistorPin.TERMINAL_A),
                right.pin(Sk9822Pin.DATA_IN),
            )
        connect(
            board, clock, left.pin(Sk9822Pin.CLOCK_OUT), right.pin(Sk9822Pin.CLOCK_IN)
        )
    no_connect(board, chain[-1].pin(Sk9822Pin.DATA_OUT))
    no_connect(board, chain[-1].pin(Sk9822Pin.CLOCK_OUT))


def _turn_termination(board: pcbnew.BOARD, led: Sk9822, reference: str) -> Resistor:
    """Place a rank-turn data terminator in line with the LED's DO pad, outward."""
    footprint = board.FindFootprintByReference(led.reference)
    if footprint is None:
        raise ValueError(f"missing LED {led.reference}")
    pad = next(
        pad for pad in footprint.Pads() if pad.GetNumber() == str(Sk9822Pin.DATA_OUT)
    )
    x = pcbnew.ToMM(pad.GetPosition().x) - native.ORIGIN_X_MM
    y = native.ORIGIN_Y_MM - pcbnew.ToMM(pad.GetPosition().y)
    centre_x = pcbnew.ToMM(footprint.GetPosition().x) - native.ORIGIN_X_MM
    outward = 1.0 if x > centre_x else -1.0
    return place(
        board,
        parts.RES_56_PART,
        reference,
        at=(x + outward * LED_TURN_TERMINATION_OFFSET_MM, y),
        assembly=LED_CHAIN_ASSEMBLY,
        purpose="LED rank-turn data source termination",
    )
