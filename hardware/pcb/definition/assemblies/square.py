"""The four-part square: explicit membership, local wiring, and placement."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from itertools import pairwise

import pcbnew

from pcb.definition.native import connect, no_connect, place
from pcb.definition.parts.catalog import (
    CAPACITOR_HALL_BYPASS_OFFSET_MM,
    CAPACITOR_LED_BYPASS_OFFSET_MM,
)
from shared import dimensions, wiring
from shared.electronics import CapacitorComponent as Capacitor
from shared.electronics import CapacitorPin, HallSensorPin, Sk9822Pin
from shared.electronics import HallSensorComponent as HallSensor
from shared.electronics import Sk9822Component as Sk9822


@dataclass(frozen=True)
class Square:
    name: str
    led: Sk9822
    hall_sensor: HallSensor


def add_square(board: pcbnew.BOARD, *, name: str, at: tuple[float, float]) -> Square:
    file, rank = wiring.parse_square(name)
    # Derive stable references from board coordinates, not insertion order.
    chain_index = rank * 8 + (file if rank % 2 == 0 else 7 - file)
    sensor_index = sensor_number(file, rank) - 1
    x, y = at
    lx, ly = x + dimensions.LED_POSITION_MM[0], y + dimensions.LED_POSITION_MM[1]
    assembly = f"square/{name}"
    led = place(
        board,
        Sk9822(f"U{6 + chain_index}"),
        part_key="SK9822",
        at=(lx, ly),
        rotation=180 if (rank + 1) % 2 == 0 else 0,
        assembly=assembly,
        library="SK9822",
        value="SK9822",
        description="Clocked 5050 RGB LED",
        extras={"Square": name, "ChainIndex": str(chain_index + 1)},
    )
    sensor = place(
        board,
        HallSensor(f"HS{1 + sensor_index}"),
        part_key="HALL_SENSOR",
        at=at,
        assembly=assembly,
        library="HALL",
        value="DRV5032FC",
        description="Omnipolar active-low Hall-effect square sensor",
        extras={"Square": name},
    )
    led_cap = place(
        board,
        Capacitor(f"C{8 + chain_index}"),
        part_key="CAP_100N",
        at=(
            lx + CAPACITOR_LED_BYPASS_OFFSET_MM[0],
            ly + CAPACITOR_LED_BYPASS_OFFSET_MM[1],
        ),
        assembly=assembly,
        library="C",
        value="100nF",
        description="Local LED decoupling capacitor",
        extras={"Square": name},
    )
    sensor_cap = place(
        board,
        Capacitor(f"C{72 + sensor_index}"),
        part_key="CAP_100N",
        at=(
            x + CAPACITOR_HALL_BYPASS_OFFSET_MM[0],
            y + CAPACITOR_HALL_BYPASS_OFFSET_MM[1],
        ),
        assembly=assembly,
        library="C",
        value="100nF",
        description="Local Hall-sensor decoupling capacitor",
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
    chain = [squares[name].led for name, _, _ in wiring.led_chain_order()]
    connect(board, wiring.LED_DATA_NET, chain[0].pin(Sk9822Pin.DATA_IN))
    connect(board, wiring.LED_CLOCK_NET, chain[0].pin(Sk9822Pin.CLOCK_IN))
    for (left, right), (data, clock) in zip(
        pairwise(chain), LED_LINK_NAMES, strict=True
    ):
        connect(board, data, left.pin(Sk9822Pin.DATA_OUT), right.pin(Sk9822Pin.DATA_IN))
        connect(
            board, clock, left.pin(Sk9822Pin.CLOCK_OUT), right.pin(Sk9822Pin.CLOCK_IN)
        )
    no_connect(board, chain[-1].pin(Sk9822Pin.DATA_OUT))
    no_connect(board, chain[-1].pin(Sk9822Pin.CLOCK_OUT))


# Fixed link names preserve stable netlist identities across builds.
LED_LINK_NAMES = (
    ("N$207", "N$208"),
    ("N$225", "N$226"),
    ("N$227", "N$228"),
    ("N$115", "N$116"),
    ("N$117", "N$118"),
    ("N$119", "N$120"),
    ("N$121", "N$122"),
    ("LED_D8", "LED_C8"),
    ("N$123", "N$124"),
    ("N$125", "N$126"),
    ("N$127", "N$128"),
    ("N$129", "N$130"),
    ("N$131", "N$132"),
    ("N$133", "N$134"),
    ("N$135", "N$136"),
    ("LED_D16", "LED_C16"),
    ("N$137", "N$138"),
    ("N$139", "N$140"),
    ("N$141", "N$142"),
    ("N$143", "N$144"),
    ("N$145", "N$146"),
    ("N$147", "N$148"),
    ("N$149", "N$150"),
    ("LED_D24", "LED_C24"),
    ("N$151", "N$152"),
    ("N$153", "N$154"),
    ("N$155", "N$156"),
    ("N$157", "N$158"),
    ("N$159", "N$160"),
    ("N$161", "N$162"),
    ("N$163", "N$164"),
    ("LED_D32", "LED_C32"),
    ("N$165", "N$166"),
    ("N$167", "N$168"),
    ("N$169", "N$170"),
    ("N$171", "N$172"),
    ("N$173", "N$174"),
    ("N$175", "N$176"),
    ("N$177", "N$178"),
    ("LED_D40", "LED_C40"),
    ("N$179", "N$180"),
    ("N$181", "N$182"),
    ("N$183", "N$184"),
    ("N$185", "N$186"),
    ("N$189", "N$190"),
    ("N$191", "N$192"),
    ("N$193", "N$194"),
    ("LED_D48", "LED_C48"),
    ("N$195", "N$196"),
    ("N$197", "N$198"),
    ("N$199", "N$200"),
    ("N$201", "N$202"),
    ("N$203", "N$204"),
    ("N$205", "N$206"),
    ("N$209", "N$210"),
    ("LED_D56", "LED_C56"),
    ("N$211", "N$212"),
    ("N$213", "N$214"),
    ("N$215", "N$216"),
    ("N$217", "N$218"),
    ("N$219", "N$220"),
    ("N$221", "N$222"),
    ("N$223", "N$224"),
)


def sensor_number(file: int, rank: int) -> int:
    """Published Hall references run row-major within each 4x4 quadrant."""
    return (rank // 4) * 32 + (file // 4) * 16 + (rank % 4) * 4 + file % 4 + 1
