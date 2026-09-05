"""Shared SN74AHCT125 pin semantics."""

from enum import StrEnum

from shared.components import AHCT125
from shared.electronics.base import ElectronicComponent


class Ahct125Pin(StrEnum):
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
