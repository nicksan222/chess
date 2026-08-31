"""Typed component identities and pins used by board-generation code."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import ClassVar, Generic, TypeVar


PinType = TypeVar("PinType", bound=StrEnum)
Endpoint = tuple[str, StrEnum]


class ComponentReference(StrEnum):
    """Semantic identities for individually addressed board components."""

    HOST_GPIO_HEADER = "J1"
    DISPLAY_HEADER = "J2"
    DC_INPUT_JACK = "J3"
    INPUT_FUSE = "F1"
    INPUT_TVS = "D1"
    MAIN_POWER_SWITCH = "SW13"
    LED_LEVEL_SHIFTER = "U5"


@dataclass(frozen=True)
class BoardComponent(Generic[PinType]):
    """A physical board component whose logical pins have semantic names."""

    reference: str
    pin_type: ClassVar[type[StrEnum]]

    def get_pins(self) -> tuple[PinType, ...]:
        """Return every logical pin as a semantic enum member."""
        return tuple(self.pin_type)  # type: ignore[return-value]

    def get_pin(self, pin: PinType) -> PinType:
        """Validate and return one of this component's pins."""
        if not isinstance(pin, self.pin_type):
            raise TypeError(
                f"{self.reference} expects {self.pin_type.__name__}, "
                f"not {type(pin).__name__}"
            )
        return pin

    def get_pin_by_number(self, number: str) -> PinType:
        """Translate a serialized datasheet number at the netlist boundary."""
        try:
            return self.pin_type(number)  # type: ignore[return-value]
        except ValueError as error:
            raise KeyError(f"{self.reference} has no logical pin {number!r}") from error

    def endpoint(self, pin: PinType) -> tuple[str, PinType]:
        """Return the typed netlist endpoint for ``pin``."""
        return self.reference, self.get_pin(pin)
