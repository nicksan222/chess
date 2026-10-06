"""A generic two-terminal diode with anode and cathode kept distinct."""

from __future__ import annotations

import math
from dataclasses import dataclass
from enum import StrEnum

from pcb.harness.base.component import BoardComponent
from pcb.harness.base.spice.model import ModelParameter, SpiceModel


class DiodePin(StrEnum):
    """Current normally enters at the anode and leaves at the cathode.

    The cathode is the marked end on many diode packages. Reversing these
    terminals changes circuit behavior, so their order is explicit.
    """

    ANODE = "1"
    CATHODE = "2"


@dataclass(frozen=True, slots=True, kw_only=True)
class Diode(BoardComponent[DiodePin]):
    """One diode with parameters for a basic exponential SPICE diode model.

    ``saturation_current_amperes`` controls the forward current curve near
    zero bias. ``ideality_factor`` adjusts its slope. ``series_resistance_ohms``
    represents internal ohmic loss. These must be selected from part evidence
    or stated modeling assumptions; a generic curve does not prove a real
    diode's reverse breakdown or surge behavior.
    """

    saturation_current_amperes: float
    ideality_factor: float
    series_resistance_ohms: float

    def __post_init__(self) -> None:
        """Reject unusable model values before automatic registration."""
        if self.definition.pin_type is not DiodePin:
            raise ValueError("diode definition must use DiodePin")
        if (
            not math.isfinite(self.saturation_current_amperes)
            or self.saturation_current_amperes <= 0
        ):
            raise ValueError("diode saturation current must be finite and positive")
        if not math.isfinite(self.ideality_factor) or self.ideality_factor <= 0:
            raise ValueError("diode ideality factor must be finite and positive")
        if (
            not math.isfinite(self.series_resistance_ohms)
            or self.series_resistance_ohms < 0
        ):
            raise ValueError("diode series resistance must be finite and nonnegative")
        super(Diode, self).__post_init__()

    def simulation_model(self) -> SpiceModel:
        """Supply the ordered diode terminals and numeric model parameters."""
        return SpiceModel(
            "diode",
            (DiodePin.ANODE, DiodePin.CATHODE),
            (
                ModelParameter(
                    "saturation_current", self.saturation_current_amperes, "ampere"
                ),
                ModelParameter("ideality_factor", self.ideality_factor, "ratio"),
                ModelParameter("series_resistance", self.series_resistance_ohms, "ohm"),
            ),
        )

    def product_parameters(self) -> tuple[object, ...]:
        """Keep the chosen model parameters consistent for one diode product."""
        return (
            self.saturation_current_amperes,
            self.ideality_factor,
            self.series_resistance_ohms,
        )
