"""Two-terminal board capacitors."""

from enum import StrEnum
from .base import BoardComponent


class CapacitorPin(StrEnum):
    SUPPLY_OR_ELECTRODE_A = "1"
    RETURN_OR_ELECTRODE_B = "2"


class Capacitor(BoardComponent[CapacitorPin]):
    pin_type = CapacitorPin
