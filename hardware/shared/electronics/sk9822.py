"""Shared SK9822 pin semantics and chain direction."""

from enum import StrEnum

from shared.components import SK9822
from shared.electronics.base import ElectronicComponent


class Sk9822Pin(StrEnum):
    DATA_IN = "1"
    CLOCK_IN = "2"
    GROUND = "3"
    FIVE_VOLTS = "4"
    CLOCK_OUT = "5"
    DATA_OUT = "6"


class Sk9822Component(ElectronicComponent[Sk9822Pin]):
    pin_type = Sk9822Pin
    specs = (SK9822,)

    @classmethod
    def input_pins(cls) -> frozenset[Sk9822Pin]:
        return frozenset((Sk9822Pin.DATA_IN, Sk9822Pin.CLOCK_IN))

    @classmethod
    def output_pins(cls) -> frozenset[Sk9822Pin]:
        return frozenset((Sk9822Pin.DATA_OUT, Sk9822Pin.CLOCK_OUT))
