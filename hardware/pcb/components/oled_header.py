"""Four-pin I2C OLED connector J2."""

from enum import StrEnum
from .base import BoardComponent, ComponentReference


class OledHeaderPin(StrEnum):
    GROUND = "1"
    THREE_VOLTS_THREE = "2"
    I2C_CLOCK = "3"
    I2C_DATA = "4"


class OledHeader(BoardComponent[OledHeaderPin]):
    pin_type = OledHeaderPin


DISPLAY_HEADER = OledHeader(ComponentReference.DISPLAY_HEADER)
