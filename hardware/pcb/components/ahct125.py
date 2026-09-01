"""SN74AHCT125 quad level-shifting buffer U5."""

from enum import StrEnum

from .base import BoardComponent, ComponentReference


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


class Ahct125(BoardComponent[Ahct125Pin]):
    pin_type = Ahct125Pin


LED_LEVEL_SHIFTER = Ahct125(ComponentReference.LED_LEVEL_SHIFTER)
