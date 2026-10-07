"""Name a device's simulation behavior without embedding simulator syntax."""

from __future__ import annotations

import math
from dataclasses import dataclass
from enum import StrEnum
from typing import cast


@dataclass(frozen=True, slots=True)
class ModelParameter:
    """One named, numeric input to a reusable electrical model.

    For example, a resistor model can receive a resistance value in ohms.
    ``unit`` is written out for the author and reviewer. The SPICE converter
    checks supported parameter names, units, and ranges before writing a model.
    No raw ngspice expression is passed through this object.
    """

    name: str
    value: float
    unit: str

    def __post_init__(self) -> None:
        """Reject a parameter with no meaning or a nonfinite value."""
        if (
            not self.name.strip()
            or not self.unit.strip()
            or not math.isfinite(self.value)
        ):
            raise ValueError("model parameter needs a name, finite value and unit")


@dataclass(frozen=True, slots=True)
class SpiceModel:
    """A reference to a reusable device behavior and its ordered terminals.

    ``key`` selects a model supported by the harness converter, such as a
    resistor or a diode. ``terminals`` tells the converter which logical
    component pins connect to the model terminals, in model-defined order. The
    component definition verifies that each listed terminal belongs to its pin
    enum. ``parameters`` supply documented numeric choices for the model.

    A valid declaration only describes the simulator's model. It does not
    confirm that the chosen model matches a real part's datasheet.
    """

    key: str
    terminals: tuple[StrEnum, ...]
    parameters: tuple[ModelParameter, ...] = ()

    def __post_init__(self) -> None:
        """Require a resolvable model identity and unambiguous terminal order."""
        if not self.key.strip() or not self.terminals:
            raise ValueError("SPICE model needs a key and at least one terminal")
        if any(not isinstance(cast(object, pin), StrEnum) for pin in self.terminals):
            raise ValueError("SPICE model terminals must be typed pin enum values")
        if len(set(self.terminals)) != len(self.terminals):
            raise ValueError("SPICE model terminals must be unique")
        names = [parameter.name for parameter in self.parameters]
        if len(set(names)) != len(names):
            raise ValueError("SPICE model parameter names must be unique")


@dataclass(frozen=True, slots=True)
class ModelOverride:
    """One scenario's documented parameter corner, without changing the part."""

    reference: str
    parameter: ModelParameter
