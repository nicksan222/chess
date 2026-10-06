"""A generic button contact with an explicit static simulation state."""

from __future__ import annotations

import math
from dataclasses import dataclass
from enum import StrEnum

from pcb.harness.base.component import BoardComponent
from pcb.harness.base.spice.model import ModelParameter, SpiceModel


class ButtonPin(StrEnum):
    """The two logical contacts of a normally open or normally closed button.

    A real four-leg tactile switch may have two physical pads for each contact;
    the later footprint definition must map those duplicated pads to these two
    logical terminals and check that the internal straps are correct.
    """

    CONTACT_A = "1"
    CONTACT_B = "2"


class ButtonState(StrEnum):
    """The contact position for one *static* simulation setup."""

    OPEN = "open"
    CLOSED = "closed"


@dataclass(frozen=True, slots=True, kw_only=True)
class Button(BoardComponent[ButtonPin]):
    """One placed button, modeled as a contact resistance in one fixed state.

    Closed and open resistances are in ohms. The open value is a very large
    finite resistance, not a true disconnected pin; this helps SPICE solve a
    circuit while approximating leakage. A press/release sequence needs a
    time-varying switch model in a later component kind.
    """

    state: ButtonState
    closed_resistance_ohms: float
    open_resistance_ohms: float

    def __post_init__(self) -> None:
        """Check state and contact values before automatic registration."""
        if self.definition.pin_type is not ButtonPin:
            raise ValueError("button definition must use ButtonPin")
        if type(self.state) is not ButtonState:
            raise ValueError("button state must be ButtonState")
        if (
            not math.isfinite(self.closed_resistance_ohms)
            or self.closed_resistance_ohms <= 0
        ):
            raise ValueError("closed resistance must be finite and positive")
        if (
            not math.isfinite(self.open_resistance_ohms)
            or self.open_resistance_ohms <= self.closed_resistance_ohms
        ):
            raise ValueError("open resistance must exceed closed resistance")
        super(Button, self).__post_init__()

    def simulation_model(self) -> SpiceModel:
        """Select the resistance appropriate to the declared static state."""
        resistance = (
            self.closed_resistance_ohms
            if self.state is ButtonState.CLOSED
            else self.open_resistance_ohms
        )
        return SpiceModel(
            "button_static",
            (ButtonPin.CONTACT_A, ButtonPin.CONTACT_B),
            (ModelParameter("contact_resistance", resistance, "ohm"),),
        )

    def product_parameters(self) -> tuple[object, ...]:
        """Share physical contact values while allowing each button's state."""
        return (self.closed_resistance_ohms, self.open_resistance_ohms)
