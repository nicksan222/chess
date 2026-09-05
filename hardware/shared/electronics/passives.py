"""Shared semantics for passive and two-terminal components."""

from enum import StrEnum

from shared.components import (
    CAP_10U,
    CAP_100N,
    CAP_1000U,
    FUSE_2A,
    POWER_SWITCH,
    RES_4K7,
    TVS_6V8,
)
from shared.electronics.base import ElectronicComponent


class CapacitorPin(StrEnum):
    SUPPLY_OR_ELECTRODE_A = "1"
    RETURN_OR_ELECTRODE_B = "2"


class CapacitorComponent(ElectronicComponent[CapacitorPin]):
    pin_type = CapacitorPin
    specs = (CAP_100N, CAP_10U, CAP_1000U)


class ResistorPin(StrEnum):
    TERMINAL_A = "1"
    TERMINAL_B = "2"


class ResistorComponent(ElectronicComponent[ResistorPin]):
    pin_type = ResistorPin
    specs = (RES_4K7,)


class FusePin(StrEnum):
    UNFUSED_INPUT = "1"
    FUSED_OUTPUT = "2"


class FuseComponent(ElectronicComponent[FusePin]):
    pin_type = FusePin
    specs = (FUSE_2A,)


class TvsDiodePin(StrEnum):
    CATHODE_FIVE_VOLTS = "1"
    ANODE_GROUND = "2"


class TvsDiodeComponent(ElectronicComponent[TvsDiodePin]):
    pin_type = TvsDiodePin
    specs = (TVS_6V8,)


class PowerSwitchPin(StrEnum):
    FUSED_INPUT = "1"
    SWITCHED_FIVE_VOLTS = "2"


class PowerSwitchComponent(ElectronicComponent[PowerSwitchPin]):
    pin_type = PowerSwitchPin
    specs = (POWER_SWITCH,)
