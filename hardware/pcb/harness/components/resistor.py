"""The first concrete, file-per-kind component built on the harness contracts."""

from __future__ import annotations

import math
from dataclasses import dataclass
from enum import StrEnum

from pcb.harness.base.component import BoardComponent
from pcb.harness.base.spice.model import ModelParameter, SpiceModel


class ResistorPin(StrEnum):
    """The two physical terminals of a nonpolarized resistor.

    Neither terminal is an input or output. Numbering still matters because a
    future footprint check must match each logical terminal to its copper pad.
    """

    TERMINAL_A = "1"
    TERMINAL_B = "2"


@dataclass(frozen=True, slots=True, kw_only=True)
class Resistor(BoardComponent[ResistorPin]):
    """One resistor including nominal electrical value and allowed variation.

    ``resistance_ohms`` is how strongly the part opposes current, in ohms.
    ``tolerance_percent`` is the manufacturer's allowed difference from that
    nominal value. Inherited fields describe the exact product, position,
    courtyard, net of each terminal and any component-owned proof requests.
    Successful construction registers the resistor with its board registry.
    """

    resistance_ohms: float
    tolerance_percent: float

    def __post_init__(self) -> None:
        """Check resistor-specific facts before base registration occurs."""
        if self.definition.pin_type is not ResistorPin:
            raise ValueError("resistor definition must use ResistorPin")
        if not math.isfinite(self.resistance_ohms) or self.resistance_ohms <= 0:
            raise ValueError("resistor resistance must be finite and positive")
        if (
            not math.isfinite(self.tolerance_percent)
            or not 0 <= self.tolerance_percent < 100
        ):
            raise ValueError("resistor tolerance must be between 0 and 100 percent")
        # Python 3.12's slots dataclass replacement makes zero-argument super()
        # refer to the pre-replacement class. Call the base explicitly here.
        super(Resistor, self).__post_init__()

    def simulation_model(self) -> SpiceModel:
        """Describe the resistor to the harness's SPICE converter.

        The component author gives physical resistance in ohms; only the
        converter later decides how an ngspice resistor line is spelled.
        """
        return SpiceModel(
            "resistor",
            (ResistorPin.TERMINAL_A, ResistorPin.TERMINAL_B),
            (ModelParameter("resistance", self.resistance_ohms, "ohm"),),
        )

    def product_parameters(self) -> tuple[object, ...]:
        """Keep nominal resistance and tolerance tied to the purchased part."""
        return (self.resistance_ohms, self.tolerance_percent)
