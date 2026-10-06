"""Shared typed pinouts for board connectors."""

from enum import StrEnum

from shared.components import OLED_HEADER
from shared.electronics.base import ElectronicComponent


class OledHeaderPin(StrEnum):
    """JST SH header pins: 1 GND, 2 +3V3, 3 SCL, 4 SDA, and two mounting tabs tied to ground."""

    GROUND = "1"
    THREE_VOLTS_THREE = "2"
    I2C_CLOCK = "3"
    I2C_DATA = "4"
    # SH reinforcement tabs, soldered for strength and tied to GND.
    MOUNTING_TAB_A = "5"
    MOUNTING_TAB_B = "6"


class OledHeaderComponent(ElectronicComponent[OledHeaderPin]):
    """Typed model of the OLED harness header (J2)."""

    pin_type = OledHeaderPin
    specs = (OLED_HEADER,)
