"""Active-low omnipolar Hall-effect square sensor."""

from enum import StrEnum

from base.component import BoardComponent


class HallSensorPin(StrEnum):
    """TI DRV5032 DBZ (SOT-23) pinout."""

    SUPPLY = "1"
    ACTIVE_LOW_OUTPUT = "2"
    GROUND = "3"


class HallSensor(BoardComponent[HallSensorPin]):
    pin_type = HallSensorPin
