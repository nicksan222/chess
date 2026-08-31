"""SK9822 LED logical pins."""

from enum import StrEnum

from .base import BoardComponent


class Sk9822Pin(StrEnum):
    FIVE_VOLTS = "1"
    GROUND = "2"
    DATA_IN = "3"
    CLOCK_IN = "4"
    DATA_OUT = "5"
    CLOCK_OUT = "6"


class Sk9822(BoardComponent[Sk9822Pin]):
    pin_type = Sk9822Pin

    @classmethod
    def input_pins(cls) -> frozenset[Sk9822Pin]:
        return frozenset((Sk9822Pin.DATA_IN, Sk9822Pin.CLOCK_IN))

    @classmethod
    def output_pins(cls) -> frozenset[Sk9822Pin]:
        return frozenset((Sk9822Pin.DATA_OUT, Sk9822Pin.CLOCK_OUT))
