"""Typed component identities and pins used by board-generation code."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import ClassVar, NamedTuple, Protocol, Self, cast


class Endpoint(NamedTuple):
    """A named, tuple-compatible netlist endpoint."""

    reference: str
    pin: StrEnum


class NetLookup(Protocol):
    """Read-only circuit interface understood by components and their pins."""

    def net_name(self, endpoint: tuple[str, str]) -> str: ...

    def peers(self, endpoint: tuple[str, str]) -> tuple[Endpoint, ...]: ...


class ConnectionSink(Protocol):
    """Mutable circuit-construction interface used by ``ComponentPin.connect``."""

    def connect(
        self,
        *pins: ComponentPin,
        name: str | None = None,
        no_connect: bool = False,
    ) -> Self: ...


@dataclass(frozen=True)
class ComponentPin[PinType: StrEnum]:
    """A pin bound to a component instance, with navigable circuit behaviour.

    Pin enums describe a product's datasheet pinout. ``ComponentPin`` adds the
    instance reference and operations, preventing routing code from manufacturing
    anonymous ``(reference, number)`` tuples.
    """

    component: BoardComponent[PinType]
    definition: PinType

    @property
    def endpoint(self) -> Endpoint:
        return Endpoint(self.component.reference, self.definition)

    @property
    def number(self) -> str:
        return self.definition.value

    def net_name(self, connections: NetLookup) -> str:
        """Return the net attached to this pin."""
        return connections.net_name(self.endpoint)

    def peers(self, connections: NetLookup) -> tuple[Endpoint, ...]:
        """Return every other pin electrically attached to this pin."""
        return connections.peers(self.endpoint)

    def is_attached_to(self, other: ComponentPin, connections: NetLookup) -> bool:
        return other.endpoint in self.peers(connections)

    def connect(
        self,
        *others: ComponentPin,
        using: ConnectionSink,
        name: str | None = None,
    ) -> None:
        """Attach this pin to ``others`` through a circuit builder."""
        using.connect(self, *others, name=name)


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

    def pin(self, pin: PinType) -> ComponentPin[PinType]:
        """Bind a semantic datasheet pin to this component instance."""
        return ComponentPin(self, self.get_pin(pin))

    @property
    def pins(self) -> tuple[ComponentPin[PinType], ...]:
        """Every pin in this component's typed pinout."""
        return tuple(self.pin(pin) for pin in self.get_pins())

    def endpoint(self, pin: PinType) -> Endpoint:
        """Return the typed netlist endpoint for ``pin``."""
        return self.pin(pin).endpoint

    def attachments(self, connections: NetLookup) -> dict[PinType, str]:
        """Resolve every semantic component pin to its attached net."""
        return {
            pin: connections.net_name(self.endpoint(pin)) for pin in self.get_pins()
        }
