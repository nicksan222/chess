"""Shared J4 power-entry header pin semantics (JST B4PS-VH)."""

from enum import StrEnum

from shared.components import POWER_HEADER
from shared.electronics.base import ElectronicComponent


class PowerHeaderPin(StrEnum):
    """Harness: 1 jack tip, 2 jack sleeve, 3 fused feed to the rocker, 4 RUN back.

    S4b: the rocker no longer carries the load; it switches the eFuse enable.
    """

    DC_INPUT = "1"
    GROUND = "2"
    FUSED_TO_SWITCH = "3"
    RUN = "4"


class PowerHeaderComponent(ElectronicComponent[PowerHeaderPin]):
    """Typed model of the J4 power-entry header."""

    pin_type = PowerHeaderPin
    specs = (POWER_HEADER,)
