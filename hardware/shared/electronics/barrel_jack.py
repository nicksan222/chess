"""Panel DC jack terminals, named as the Switchcraft 722A drawing labels them.

The jack is off-board (wired to J4), so these names matter to the harness definition
and its tests, not to a footprint.
"""

from enum import StrEnum

from shared.components import BARREL_JACK
from shared.electronics.base import ElectronicComponent


class BarrelJackPin(StrEnum):
    """Logical terminals of the panel jack, as the Switchcraft drawing labels them (centre pin = supply positive, sleeve = ground, sleeve shunt unused)."""

    CENTRE_POSITIVE = "CENTER PIN"
    SLEEVE_GROUND = "SLEEVE"
    SWITCHED_SLEEVE_GROUND = "SLEEVE SHUNT"


class BarrelJackPad(StrEnum):
    """The same terminal names as physical lugs (the jack is off-board, so only the harness uses them)."""

    CENTRE_POSITIVE = "CENTER PIN"
    SLEEVE_GROUND = "SLEEVE"
    SWITCHED_SLEEVE_GROUND = "SLEEVE SHUNT"


class BarrelJackComponent(ElectronicComponent[BarrelJackPin]):
    """Typed model of the panel jack, used by the harness definition and tests."""

    pin_type = BarrelJackPin
    specs = (BARREL_JACK,)
