"""No floating CMOS input, no undriven open-drain net, rails on rail pins.

Pin electrical types are hand-typed from the datasheets cited in
`test_land_patterns.py`: TI SCPS233E §5 (TCA9554: P-ports push-pull I/O with an
internal 100 kOhm pull-up, INT and SDA open-drain), TI SCLS264R Table 4-1 and note
"all unused inputs must be held at VCC or GND" (SN74AHCT125: nOE active-low input),
TI SLVSDC7H Table 4-1 (DRV5032FC: open-drain output), Opsco SPC/SK9822-A §5 and the
Raspberry Pi 40-pin header (GPIO, 3V3 output, 5V input). Parts without logic pins
(passives, switches, connectors to off-board modules) are passive.
"""

import unittest
from collections.abc import Collection, Mapping, Sequence
from typing import ClassVar

from pcb.definition import board, native
from pcb.definition.parts.catalog import PCB_PARTS
from pcb.definition.verification import ASSUMPTIONS

INPUT = "input"
OUTPUT = "output"
TRISTATE = "tristate output"
OPEN_DRAIN = "open-drain output"
IO_PULLUP = "I/O with internal pull-up"
HOST_GPIO = "host GPIO"
POWER = "power input"
POWER_OUT = "power output"
GROUND = "ground"
# Analog pin set by an external resistor or capacitor (TPS25947 EN/UVLO, OVLO,
# PGTH, ILM, DVDT, ITIMER: "Do not leave floating", SLVSFC9C Table 5-1).
ANALOG = "analog, set by an external R or C"

RAILS = frozenset({"+5V", "+3V3", "LED_5V"})

PIN_TYPES: Mapping[str, Mapping[str, str]] = {
    "SK9822": {
        "1": INPUT,
        "2": INPUT,
        "3": GROUND,
        "4": POWER,
        "5": OUTPUT,
        "6": OUTPUT,
    },
    "TCA9554": {
        "1": INPUT,
        "2": INPUT,
        "3": INPUT,
        **{pin: IO_PULLUP for pin in ("4", "5", "6", "7", "9", "10", "11", "12")},
        "8": GROUND,
        "13": OPEN_DRAIN,
        "14": INPUT,
        "15": OPEN_DRAIN,
        "16": POWER,
    },
    "AHCT125": {
        **{pin: INPUT for pin in ("1", "2", "4", "5", "9", "10", "12", "13")},
        **{pin: TRISTATE for pin in ("3", "6", "8", "11")},
        "7": GROUND,
        "14": POWER,
    },
    "HALL_SENSOR": {"1": POWER, "2": OPEN_DRAIN, "3": GROUND},
    # TI SLVSFC9C Table 5-1 (TPS259474ARPW): PG open-drain, IN supply, OUT output.
    "EFUSE": {
        **{pin: ANALOG for pin in ("1", "2", "4", "7", "9", "10")},
        "3": OPEN_DRAIN,
        "5": POWER,
        "6": POWER_OUT,
        "8": GROUND,
    },
    # S6 LED switch: Vishay Si4403DDY (1-3 S, 4 G, 5-8 D); onsemi BSS138LT1G
    # (1 G, 2 S, 3 D). Q1's gate is set by R16/C145; Q2's drain is open-drain.
    "LED_SWITCH": {
        **{pin: POWER for pin in ("1", "2", "3")},
        "4": ANALOG,
        **{pin: POWER_OUT for pin in ("5", "6", "7", "8")},
    },
    "LED_SWITCH_DRIVER": {"1": INPUT, "2": GROUND, "3": OPEN_DRAIN},
    # TI SN74LVC1G97 DBV (S6b H6): In1 (tied high), In0, In2 inputs; Y push-pull.
    "LED_ENABLE_GATE": {
        "1": INPUT,
        "2": GROUND,
        "3": INPUT,
        "4": OUTPUT,
        "5": POWER,
        "6": INPUT,
    },
    "PI_ZERO_HEADER": {
        **{str(pin): HOST_GPIO for pin in range(1, 41)},
        "1": POWER_OUT,
        "17": POWER_OUT,
        "2": POWER,
        "4": POWER,
        **{str(pin): GROUND for pin in (6, 9, 14, 20, 25, 30, 34, 39)},
    },
}
DRIVERS = frozenset({OUTPUT, TRISTATE, HOST_GPIO, POWER_OUT})
PUSH_PULL = frozenset({OUTPUT, TRISTATE})
MAY_FLOAT = frozenset({OUTPUT, TRISTATE, OPEN_DRAIN, IO_PULLUP, HOST_GPIO})
# Passive parts that can set an ANALOG pin.
SETTING_PREFIXES = ("RES_", "CAP_")
# Supply pins and the rail each must sit on (same datasheets as above).
POWER_RAILS: Mapping[tuple[str, str], str] = {
    ("SK9822", "4"): "LED_5V",
    ("TCA9554", "16"): "+3V3",
    ("AHCT125", "14"): "+5V",
    ("HALL_SENSOR", "1"): "+3V3",
    ("PI_ZERO_HEADER", "2"): "+5V",
    ("PI_ZERO_HEADER", "4"): "+5V",
    ("PI_ZERO_HEADER", "1"): "+3V3",
    ("PI_ZERO_HEADER", "17"): "+3V3",
    ("EFUSE", "5"): "DC_FUSED",
    ("EFUSE", "6"): "+5V",
    **{("LED_SWITCH", pin): "+5V" for pin in ("1", "2", "3")},
    **{("LED_SWITCH", pin): "LED_5V" for pin in ("5", "6", "7", "8")},
    ("LED_ENABLE_GATE", "5"): "+5V",
}
# Raspberry Pi documentation: GPIO2/3 (header pins 3/5) carry fixed 1.8 kOhm pull-ups.
# Any other host GPIO is biased only by firmware.
HOST_PULLED_PINS = frozenset({"3", "5"})
# Host pins the firmware drives push-pull (SPI0 MOSI/SCLK, spidev; S6 LED_EN on
# pin 37, a typed output in pins.rs): they count as drivers.
HOST_PUSH_PULL_PINS = frozenset({"19", "23", "37"})
# Parts with no logic pins (passives, switches, test points, off-board connectors).
