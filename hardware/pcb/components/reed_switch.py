"""Normally-open square sensor reed switches."""

from enum import StrEnum
from .base import BoardComponent


class ReedSwitchPin(StrEnum):
    SENSE_CONTACT = "1"
    GROUND_CONTACT = "2"


class ReedSwitch(BoardComponent[ReedSwitchPin]):
    pin_type = ReedSwitchPin
