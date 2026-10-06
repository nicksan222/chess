"""Shared semantics for passive and two-terminal components.

Role: pin enums and typed models for capacitors, resistors, the fuse, TVS and rocker, so
assemblies connect `part.pin(ResistorPin.TERMINAL_A)` rather than bare numbers. One model
class covers every catalogue part of a kind (`specs`).
"""

from enum import StrEnum

from shared.components import (
    CAP_1N,
    CAP_1U,
    CAP_10N,
    CAP_10U,
    CAP_100N,
    CAP_560U,
    FUSE_2A,
    POWER_SWITCH,
    RES_1K,
    RES_1K65,
    RES_10K,
    RES_56,
    RES_100K,
    RES_169K_PRECISION,
    RES_261K,
    RES_604K_PRECISION,
    TVS_12V0,
)
from shared.electronics.base import ElectronicComponent


class CapacitorPin(StrEnum):
    """Two terminals; for polarized parts pin 1 is the positive electrode, for supply decoupling pin 1 faces the rail."""

    SUPPLY_OR_ELECTRODE_A = "1"
    RETURN_OR_ELECTRODE_B = "2"


class CapacitorComponent(ElectronicComponent[CapacitorPin]):
    """Typed model of every capacitor in the catalogue."""

    pin_type = CapacitorPin
    specs = (CAP_100N, CAP_10U, CAP_560U, CAP_10N, CAP_1N, CAP_1U)


class ResistorPin(StrEnum):
    """The two terminals of a resistor (symmetric)."""

    TERMINAL_A = "1"
    TERMINAL_B = "2"


class ResistorComponent(ElectronicComponent[ResistorPin]):
    """Typed model of every resistor in the catalogue."""

    pin_type = ResistorPin
    specs = (
        RES_1K,
        RES_10K,
        RES_100K,
        RES_56,
        RES_1K65,
        RES_261K,
        RES_604K_PRECISION,
        RES_169K_PRECISION,
    )


class FusePin(StrEnum):
    """Fuse terminals: unfused input and fused output."""

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
