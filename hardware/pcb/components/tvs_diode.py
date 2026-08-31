"""Unidirectional input transient suppressor D1."""

from enum import StrEnum
from .base import BoardComponent, ComponentReference


class TvsDiodePin(StrEnum):
    CATHODE_FIVE_VOLTS = "1"
    ANODE_GROUND = "2"


class TvsDiode(BoardComponent[TvsDiodePin]):
    pin_type = TvsDiodePin


INPUT_TVS = TvsDiode(ComponentReference.INPUT_TVS)
