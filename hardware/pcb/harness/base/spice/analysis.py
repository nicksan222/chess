"""Specify the electrical question to ask of a simulated circuit."""

from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class OperatingPoint:
    """Solve the settled direct-current state of the circuit.

    This has no time axis. It is appropriate for supply rails, bias points and
    static pin levels after all sources have reached their stated DC values.
    """


@dataclass(frozen=True, slots=True)
class Transient:
    """Follow circuit voltages and currents over a defined time interval.

    ``duration_seconds`` is the total simulated time. ``max_step_seconds``
    bounds how far the solver may advance between saved points so short events
    are not skipped. Both are positive physical times, not ngspice commands.
    """

    duration_seconds: float
    max_step_seconds: float

    def __post_init__(self) -> None:
        """Require a positive interval with a step no longer than the interval."""
        if (
            not math.isfinite(self.duration_seconds)
            or not math.isfinite(self.max_step_seconds)
            or self.duration_seconds <= 0
            or not 0 < self.max_step_seconds <= self.duration_seconds
        ):
            raise ValueError("transient duration and step must be positive and ordered")


@dataclass(frozen=True, slots=True)
class AcSweep:
    """Measure small-signal response across a logarithmic frequency range.

    The solver first finds a DC operating point, then perturbs the circuit at
    frequencies from ``start_hz`` to ``stop_hz``. ``points_per_decade`` controls
    the resolution of that sweep. At least one independent voltage source must
    declare an AC magnitude; otherwise the small-signal circuit has no input
    stimulus. The sweep is linearized around the computed DC operating point,
    so it does not model large signal switching or nonlinear distortion.
    """

    start_hz: float
    stop_hz: float
    points_per_decade: int

    def __post_init__(self) -> None:
        """Reject a reversed or underspecified frequency sweep."""
        if type(self.points_per_decade) is not int:
            raise ValueError("AC sweep resolution must be an integer count")
        if (
            not math.isfinite(self.start_hz)
            or not math.isfinite(self.stop_hz)
            or self.start_hz <= 0
            or self.stop_hz <= self.start_hz
            or self.points_per_decade <= 0
        ):
            raise ValueError("AC sweep needs increasing frequencies and resolution")


type Analysis = OperatingPoint | Transient | AcSweep
