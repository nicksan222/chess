"""Shared TI DRV5032 pin semantics.

Role: pin names for the three-pin SOT-23 Hall sensor. The output is active-low and
open-drain, so it needs a pull-up (supplied by the expander input, see
`parts/tca9554.py`). Pinout from TI SLVSDC7H (1 supply, 2 output, 3 ground).
"""

from enum import StrEnum

from shared.components import HALL_SENSOR
from shared.electronics.base import ElectronicComponent


class HallSensorPin(StrEnum):
    SUPPLY = "1"
    ACTIVE_LOW_OUTPUT = "2"
    GROUND = "3"


class HallSensorComponent(ElectronicComponent[HallSensorPin]):
    pin_type = HallSensorPin
    specs = (HALL_SENSOR,)
