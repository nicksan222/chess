"""A complete named simulation setup, registered with an explicit board."""

from __future__ import annotations

import math
import re
from dataclasses import dataclass
from typing import TYPE_CHECKING, cast

from ..net import Net
from .analysis import AcSweep, Analysis, OperatingPoint, Transient
from .model import ModelOverride
from .source import Source
from .state import ComponentState

if TYPE_CHECKING:
    from ..registry import BoardRegistry


@dataclass(frozen=True, slots=True)
class SpiceScenario:
    """A test circuit's analysis, sources, reference ground and temperature.

    The scenario holds environmental conditions that can be shared by checks
    from many components. It registers itself with ``registry`` on successful
    construction. The harness derives device connections from the board's
    components, applies these stimuli, runs the selected analysis, and
    evaluates component-owned requirements. Nothing here is ngspice syntax.
    A passing scenario checks only the declared model and conditions; it cannot
    establish that the physical board behaves the same way.
    """

    registry: BoardRegistry
    name: str
    purpose: str
    ground_net: Net
    analysis: Analysis
    sources: tuple[Source, ...]
    temperature_celsius: float = 25.0
    component_references: tuple[str, ...] | None = None
    states: tuple[ComponentState, ...] = ()
    model_overrides: tuple[ModelOverride, ...] = ()

    def __post_init__(self) -> None:
        """Reject ambiguous setup before it enters the board's scenario list."""
        if not re.fullmatch(r"[A-Za-z][A-Za-z0-9_-]*", self.name):
            raise ValueError("scenario needs a safe name")
        if not self.purpose.strip():
            raise ValueError("scenario needs a purpose")
        if not isinstance(cast(object, self.ground_net), Net):
            raise ValueError("scenario ground must be a Net enum member")
        if not math.isfinite(self.temperature_celsius):
            raise ValueError("scenario temperature must be finite")
        if not isinstance(self.analysis, (OperatingPoint, Transient, AcSweep)):  # pyright: ignore[reportUnnecessaryIsInstance]
            raise ValueError("scenario needs a supported analysis")
        names = [source.name for source in self.sources]
        if len(set(names)) != len(names):
            raise ValueError("scenario source names must be unique")
        self.registry.register_scenario(self)
