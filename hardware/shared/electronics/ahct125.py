"""Shared SN74AHCT125 pin semantics.

Role: names every package pin by function so wiring code uses
`Ahct125Pin.BUFFER_1_INPUT` instead of a bare number. U5 uses channels 1 and 2
(SPI data and clock, 3.3 V in to 5 V out); channels 3-4 are unused. Pinout checked
by `tests/board/test_land_patterns.py` against TI SCLS264R.
"""

from enum import StrEnum

from shared.components import AHCT125
from shared.electronics.base import ElectronicComponent


class Ahct125Pin(StrEnum):
    """Pin numbers of the 14-pin package; each buffer has input, output and an enable."""

    BUFFER_1_OUTPUT_ENABLE = "1"
    BUFFER_1_INPUT = "2"
    BUFFER_1_OUTPUT = "3"
    BUFFER_2_OUTPUT_ENABLE = "4"
    BUFFER_2_INPUT = "5"
    BUFFER_2_OUTPUT = "6"
    GROUND = "7"
    BUFFER_3_OUTPUT = "8"
    BUFFER_3_INPUT = "9"
    BUFFER_3_OUTPUT_ENABLE = "10"
    BUFFER_4_OUTPUT = "11"
    BUFFER_4_INPUT = "12"
    BUFFER_4_OUTPUT_ENABLE = "13"
    SUPPLY = "14"


class Ahct125Component(ElectronicComponent[Ahct125Pin]):
    """KiCad-independent behavior of the approved level shifter."""

    pin_type = Ahct125Pin
    specs = (AHCT125,)
