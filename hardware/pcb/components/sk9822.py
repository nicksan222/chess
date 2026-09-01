"""SK9822 LED logical pins."""

from enum import StrEnum

from base.component import BoardComponent


class Sk9822Pin(StrEnum):
    """5050 pinout from the manufacturer's SK9822 specification, section 5."""

    DATA_IN = "1"
    CLOCK_IN = "2"
    GROUND = "3"
    FIVE_VOLTS = "4"
    CLOCK_OUT = "5"
    DATA_OUT = "6"


class Sk9822(BoardComponent[Sk9822Pin]):
    pin_type = Sk9822Pin

    @classmethod
    def input_pins(cls) -> frozenset[Sk9822Pin]:
        return frozenset((Sk9822Pin.DATA_IN, Sk9822Pin.CLOCK_IN))

    @classmethod
    def output_pins(cls) -> frozenset[Sk9822Pin]:
        return frozenset((Sk9822Pin.DATA_OUT, Sk9822Pin.CLOCK_OUT))
