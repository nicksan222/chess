"""Shared logical and physical terminal identities for panel buttons."""

from enum import StrEnum

from shared.components import BUTTON
from shared.electronics.base import ElectronicComponent


class TactileSwitchPin(StrEnum):
    SIGNAL = "1"
    GROUND = "2"


class TactileSwitchPad(StrEnum):
    SIGNAL_PRIMARY = "1"
    SIGNAL_DUPLICATE = "1b"
    GROUND_PRIMARY = "2"
    GROUND_DUPLICATE = "2b"


class TactileSwitchComponent(ElectronicComponent[TactileSwitchPin]):
    pin_type = TactileSwitchPin
    specs = (BUTTON,)
