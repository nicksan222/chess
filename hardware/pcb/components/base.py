"""Typed component identities and pins used by board-generation code."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import ClassVar, NamedTuple, Protocol, cast


class Endpoint(NamedTuple):
    """A named, tuple-compatible netlist endpoint."""

    reference: str
    pin: StrEnum


class NetLookup(Protocol):
    """Minimal connection-graph interface understood by component instances."""

    def net_name(self, endpoint: tuple[str, str]) -> str: ...


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
class BoardComponent[PinType: StrEnum]:
    """A physical board component whose logical pins have semantic names."""

    reference: str
    pin_type: ClassVar[type[StrEnum]]

    def get_pins(self) -> tuple[PinType, ...]:
        """Return every logical pin as a semantic enum member."""
        return cast(tuple[PinType, ...], tuple(self.pin_type))

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
            return cast(PinType, self.pin_type(number))
        except ValueError as error:
            raise KeyError(f"{self.reference} has no logical pin {number!r}") from error

    def endpoint(self, pin: PinType) -> Endpoint:
        """Return the typed netlist endpoint for ``pin``."""
        return Endpoint(self.reference, self.get_pin(pin))

    def attachments(self, connections: NetLookup) -> dict[PinType, str]:
        """Resolve every semantic component pin to its attached net."""
        return {
            pin: connections.net_name(self.endpoint(pin)) for pin in self.get_pins()
        }
