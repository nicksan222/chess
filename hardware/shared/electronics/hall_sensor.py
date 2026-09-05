"""Shared TI DRV5032 pin semantics."""

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
