"""KiCad-independent electronic component and connection behavior.

A component's datasheet identity and pin semantics are useful to PCB, CAD, test,
and firmware tooling.  They live here; domain adapters subclass these definitions
instead of copying pin numbers or constructing anonymous endpoint tuples.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Generic, NamedTuple, Protocol, TypeVar

from shared.components import ComponentSpec

PinType = TypeVar("PinType", bound=StrEnum)
EndpointPinType_co = TypeVar("EndpointPinType_co", bound=str, covariant=True)


class Endpoint(NamedTuple, Generic[EndpointPinType_co]):  # noqa: UP046
    """A component reference paired with one semantic datasheet pin."""

    reference: str
    pin: EndpointPinType_co


class BoundPin(Protocol):
    """A component pin bound to a concrete reference."""

    @property
    def endpoint(self) -> Endpoint[str]: ...


class EndpointResolver(Protocol):
    """Non-generic view used to store heterogeneous component models safely."""

    reference: str

    @property
    def pins(self) -> tuple[BoundPin, ...]: ...

    def resolve_endpoint(self, number: str) -> Endpoint[str]: ...

    def bind_pin(self, number: str) -> BoundPin: ...


@dataclass(frozen=True)
class ComponentPin(Generic[PinType]):  # noqa: UP046
    """One semantic pin bound to a concrete component instance."""

    component: ElectronicComponent[PinType]
    definition: PinType

    @property
    def endpoint(self) -> Endpoint[PinType]:
        return Endpoint(self.component.reference, self.definition)


class ComponentReference(StrEnum):
    """Semantic identities for individually addressed board components."""

    HOST_GPIO_HEADER = "J1"
    DISPLAY_HEADER = "J2"
    DC_INPUT_JACK = "J3"
    INPUT_FUSE = "F1"
    INPUT_TVS = "D1"
    MAIN_POWER_SWITCH = "SW13"
    LED_LEVEL_SHIFTER = "U5"


class ElectronicComponent(Generic[PinType]):  # noqa: UP046
    """Shared base for an exact component family and its typed pinout."""

    pin_type: type[PinType]
    specs: tuple[ComponentSpec, ...]

    def __init__(self, reference: str) -> None:
        if not reference:
            raise ValueError("component reference must not be empty")
        if not self.specs:
            raise TypeError(
                f"{type(self).__name__} must own an approved component spec"
            )
        self.reference = reference

    @classmethod
    def supports_part_key(cls, part_key: str) -> bool:
        return any(spec.key == part_key for spec in cls.specs)

    def get_pins(self) -> tuple[PinType, ...]:
        return tuple(self.pin_type)

    def get_pin(self, pin: PinType) -> PinType:
        if not isinstance(pin, self.pin_type):
            raise TypeError(
                f"{self.reference} expects {self.pin_type.__name__}, "
                f"not {type(pin).__name__}"
            )
        return pin

    def get_pin_by_number(self, number: str) -> PinType:
        try:
            return self.pin_type(number)
        except ValueError as error:
            raise KeyError(f"{self.reference} has no logical pin {number!r}") from error

    def pin(self, pin: PinType) -> ComponentPin[PinType]:
        return ComponentPin(self, self.get_pin(pin))

    def bind_pin(self, number: str) -> ComponentPin[PinType]:
        """Bind a serialized pin only at the validated input boundary."""
        return self.pin(self.get_pin_by_number(number))

    @property
    def pins(self) -> tuple[ComponentPin[PinType], ...]:
        return tuple(self.pin(pin) for pin in self.get_pins())

    def endpoint(self, pin: PinType) -> Endpoint[PinType]:
        return self.pin(pin).endpoint

    def resolve_endpoint(self, number: str) -> Endpoint[PinType]:
        return self.endpoint(self.get_pin_by_number(number))
