"""Shared logical and physical terminal identities for panel buttons.

Role: separates the two *logical* pins of a button (signal, ground) from its four
*physical* through-hole pads. On the TL1105 (E-Switch datasheet p25) leads 1-2 and 3-4
(6.5 mm apart, across the body) are internally connected and the dome bridges the
pairs (4.5 mm, same side). So each logical pin has a primary and a duplicate pad
("1"/"1b", "2"/"2b"); both pads of a pair get the same net (`native.logical_pin`).
"""

from enum import StrEnum

from shared.components import BUTTON
from shared.electronics.base import ElectronicComponent


class TactileSwitchPin(StrEnum):
    """Logical terminals seen by wiring code."""

    SIGNAL = "1"
    GROUND = "2"


class TactileSwitchPad(StrEnum):
    """Physical pad names in the footprint (see `parts/button.py`)."""

    SIGNAL_PRIMARY = "1"
    SIGNAL_DUPLICATE = "1b"
    GROUND_PRIMARY = "2"
    GROUND_DUPLICATE = "2b"


class TactileSwitchComponent(ElectronicComponent[TactileSwitchPin]):
    pin_type = TactileSwitchPin
    specs = (BUTTON,)
