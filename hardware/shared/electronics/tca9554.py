"""Shared TI TCA9554 pin semantics and GPIO behavior."""

from enum import StrEnum

from shared.components import TCA9554
from shared.electronics.base import ElectronicComponent


class Tca9554Pin(StrEnum):
    ADDRESS_0 = "1"
    ADDRESS_1 = "2"
    ADDRESS_2 = "3"
    P0 = "4"
    P1 = "5"
    P2 = "6"
    P3 = "7"
    GROUND = "8"
    P4 = "9"
    P5 = "10"
    P6 = "11"
    P7 = "12"
    INTERRUPT = "13"
    I2C_CLOCK = "14"
    I2C_DATA = "15"
    SUPPLY = "16"


class Tca9554Component(ElectronicComponent[Tca9554Pin]):
    pin_type = Tca9554Pin
    specs = (TCA9554,)

    @staticmethod
    def input_pins() -> tuple[Tca9554Pin, ...]:
        return tuple(Tca9554Pin[f"P{index}"] for index in range(8))
