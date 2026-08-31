"""Domain-neutral component identities shared by schematic, PCB, and CAD.

A specification says *what the real part is*.  Domain implementations say how
that part is drawn, placed, routed, or modelled.  This keeps package names and
physical envelopes independent from Schemdraw, Gerbonara, Blender, or KiCad.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Generic, TypeVar


@dataclass(frozen=True)
class ComponentSpec:
    """Stable identity and physical contract for one purchasable component."""

    key: str
    description: str
    package: str
    body_mm: tuple[float, float, float] | None = None
    datasheet: str = ""


Implementation = TypeVar("Implementation")


class ComponentImplementation(ABC, Generic[Implementation]):
    """Base class for a CAD, schematic, PCB, or KiCad representation."""

    spec: ComponentSpec

    def __init__(self, spec: ComponentSpec) -> None:
        self.spec = spec

    @abstractmethod
    def build(self) -> Implementation:
        """Build the domain-specific representation of :attr:`spec`."""


SK9822 = ComponentSpec(
    key="SK9822",
    description="Clocked 5050 RGB LED",
    package="LED-SK9822-6",
    body_mm=(5.4, 5.0, 1.57),
)
REED_SWITCH = ComponentSpec(
    key="REED_SWITCH",
    description="Normally-open through-hole reed switch",
    package="REED-14MM",
    body_mm=(14.0, 2.2, 2.2),
)
PI_ZERO_HEADER = ComponentSpec(
    key="PI_ZERO_HEADER",
    description="Raspberry Pi Zero 2 W 2x20 header",
    package="HDR-2X20-2.54",
)

COMPONENTS = {spec.key: spec for spec in (SK9822, REED_SWITCH, PI_ZERO_HEADER)}
