"""Describe what a simulation must measure and what result is acceptable."""

from __future__ import annotations

import math
from dataclasses import dataclass
from enum import StrEnum
from typing import cast

from ..connections import Endpoint


@dataclass(frozen=True, slots=True)
class VoltageAt:
    """Measure one component pin's voltage relative to the scenario ground net."""

    pin: Endpoint


@dataclass(frozen=True, slots=True)
class VoltageBetween:
    """Measure the first pin's voltage minus the second pin's voltage."""

    positive: Endpoint
    negative: Endpoint

    def __post_init__(self) -> None:
        """A voltage difference needs two distinct observation points."""
        if self.positive == self.negative:
            raise ValueError("voltage measurement needs distinct endpoints")


@dataclass(frozen=True, slots=True)
class CurrentThrough:
    """Measure current through a named simulation source.

    The sign follows the source's declared direction. Current through an
    arbitrary device needs an explicit model or sensing element and is outside
    this initial measurement vocabulary.
    """

    source: str

    def __post_init__(self) -> None:
        """Refuse a current measurement with no source identity."""
        if not self.source.strip():
            raise ValueError("current measurement needs a source name")


type Measurement = VoltageAt | VoltageBetween | CurrentThrough


class Observation(StrEnum):
    """How to reduce an analysis result to one number for a pass/fail check.

    ``FINAL`` takes the last point of a transient run; ``MINIMUM`` and
    ``MAXIMUM`` inspect the whole run. An operating point has just one value.
    Frequency-domain results will need a richer measurement type later.
    """

    SINGLE = "single"
    FINAL = "final"
    MINIMUM = "minimum"
    MAXIMUM = "maximum"


@dataclass(frozen=True, slots=True)
class Limit:
    """An inclusive numerical pass band for one measurement.

    The measurement determines the unit: volts for voltage, amperes for source
    current. The bounds may include zero or negative values because polarity
    and current direction matter in electrical circuits.
    """

    minimum: float
    maximum: float

    def __post_init__(self) -> None:
        """Reject limits that cannot be compared with a measured number."""
        if (
            not math.isfinite(self.minimum)
            or not math.isfinite(self.maximum)
            or self.minimum > self.maximum
        ):
            raise ValueError("measurement limit needs finite, ordered bounds")


@dataclass(frozen=True, slots=True)
class SpiceRequirement:
    """A component-owned, named claim to prove in one simulation scenario.

    ``scenario`` points to the setup that supplies operating conditions.
    ``measurement`` says what to read, ``observation`` says which point or
    extreme to use, and ``allowed`` states the pass band. ``rationale`` explains
    why it matters, ideally with a datasheet section or a stated assumption.
    A requirement is a proposed check; it is not a simulation result.
    """

    scenario: str
    measurement: Measurement
    observation: Observation
    allowed: Limit
    rationale: str
    at_seconds: float | None = None

    def __post_init__(self) -> None:
        """Keep each requested proof identifiable and explainable."""
        if not self.scenario.strip() or not self.rationale.strip():
            raise ValueError("SPICE requirement needs a scenario and rationale")
        if self.at_seconds is not None and (
            not math.isfinite(self.at_seconds) or self.at_seconds < 0
        ):
            raise ValueError("sample time must be finite and nonnegative")
        if not isinstance(
            cast(object, self.measurement), (VoltageAt, VoltageBetween, CurrentThrough)
        ):
            raise ValueError("SPICE requirement needs a supported measurement")
        if not isinstance(cast(object, self.observation), Observation):
            raise ValueError("SPICE requirement needs an observation mode")
