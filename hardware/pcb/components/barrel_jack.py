"""Centre-positive DC input jack J3."""

from enum import StrEnum

from .base import BoardComponent, ComponentReference


class BarrelJackPin(StrEnum):
    """PJ-102A terminal numbering from the Same Sky mechanical drawing."""

    CENTRE_POSITIVE = "1"
    SLEEVE_GROUND = "2"
    SWITCHED_SLEEVE_GROUND = "3"


class BarrelJackPad(StrEnum):
    CENTRE_POSITIVE = "1"
    SLEEVE_GROUND = "2"
    SWITCHED_SLEEVE_GROUND = "3"


class BarrelJack(BoardComponent[BarrelJackPin]):
    pin_type = BarrelJackPin


DC_INPUT_JACK = BarrelJack(ComponentReference.DC_INPUT_JACK)
