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
