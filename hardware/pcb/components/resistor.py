"""Two-terminal board resistors."""

from enum import StrEnum
from .base import BoardComponent


class ResistorPin(StrEnum):
    TERMINAL_A = "1"
    TERMINAL_B = "2"


class Resistor(BoardComponent[ResistorPin]):
    pin_type = ResistorPin
