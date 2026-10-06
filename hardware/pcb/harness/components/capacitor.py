"""A generic nonpolarized capacitor described without PCB or SPICE syntax."""

from __future__ import annotations

import math
from dataclasses import dataclass
from enum import StrEnum

from pcb.harness.base.component import BoardComponent
from pcb.harness.base.spice.model import ModelParameter, SpiceModel


class CapacitorPin(StrEnum):
    """The two interchangeable terminals of a nonpolarized capacitor."""

    TERMINAL_A = "1"
    TERMINAL_B = "2"


@dataclass(frozen=True, slots=True, kw_only=True)
class Capacitor(BoardComponent[CapacitorPin]):
    """One placed capacitor with nominal charge storage and voltage rating.

    Capacitance is in farads. The rating is the maximum intended working
    voltage, in volts; declaring it does not prove the board stays below it.
    The basic SPICE model is an ideal capacitor without ESR or leakage, so
    more detailed kinds can override ``simulation_model`` later.
    """

    capacitance_farads: float
    rated_volts: float

    def __post_init__(self) -> None:
        """Validate capacitor facts before automatic board registration."""
        if self.definition.pin_type is not CapacitorPin:
            raise ValueError("capacitor definition must use CapacitorPin")
        if not math.isfinite(self.capacitance_farads) or self.capacitance_farads <= 0:
            raise ValueError("capacitance must be finite and positive")
        if not math.isfinite(self.rated_volts) or self.rated_volts <= 0:
            raise ValueError("rated voltage must be finite and positive")
        super(Capacitor, self).__post_init__()

    def simulation_model(self) -> SpiceModel:
        """Pass the physical capacitance to the harness's capacitor converter."""
        return SpiceModel(
            "capacitor",
            (CapacitorPin.TERMINAL_A, CapacitorPin.TERMINAL_B),
            (ModelParameter("capacitance", self.capacitance_farads, "farad"),),
        )

    def product_parameters(self) -> tuple[object, ...]:
        """Tie capacitance and working-voltage rating to the selected item."""
        return (self.capacitance_farads, self.rated_volts)
