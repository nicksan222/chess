"""Shared typed pinouts for board connectors."""

from enum import StrEnum

from shared.components import OLED_HEADER
from shared.electronics.base import ElectronicComponent


class OledHeaderPin(StrEnum):
    GROUND = "1"
    THREE_VOLTS_THREE = "2"
    I2C_CLOCK = "3"
    I2C_DATA = "4"


class OledHeaderComponent(ElectronicComponent[OledHeaderPin]):
    pin_type = OledHeaderPin
    specs = (OLED_HEADER,)
