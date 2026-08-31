"""Four-leg tactile switches used by the control panel."""

from enum import StrEnum

from .base import BoardComponent


class TactileSwitchPin(StrEnum):
    SIGNAL = "1"
    GROUND = "2"


class TactileSwitchPad(StrEnum):
    SIGNAL_PRIMARY = "1"
    SIGNAL_DUPLICATE = "1b"
    GROUND_PRIMARY = "2"
    GROUND_DUPLICATE = "2b"


class TactileSwitch(BoardComponent[TactileSwitchPin]):
    pin_type = TactileSwitchPin
