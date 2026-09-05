"""Shared Same Sky PJ-102A terminal semantics."""

from enum import StrEnum

from shared.components import BARREL_JACK
from shared.electronics.base import ElectronicComponent


class BarrelJackPin(StrEnum):
    CENTRE_POSITIVE = "1"
    SLEEVE_GROUND = "2"
    SWITCHED_SLEEVE_GROUND = "3"


class BarrelJackPad(StrEnum):
    CENTRE_POSITIVE = "1"
    SLEEVE_GROUND = "2"
    SWITCHED_SLEEVE_GROUND = "3"


class BarrelJackComponent(ElectronicComponent[BarrelJackPin]):
    pin_type = BarrelJackPin
    specs = (BARREL_JACK,)
