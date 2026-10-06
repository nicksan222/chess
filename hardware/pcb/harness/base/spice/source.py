"""Describe electrical supplies and stimuli in physical units."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import cast

from ..net import Net


@dataclass(frozen=True, slots=True)
class DcVoltage:
    """A constant voltage difference between a source's positive and negative nets."""

    volts: float

    def __post_init__(self) -> None:
        """Keep a source's stated voltage numeric and finite."""
        if not math.isfinite(self.volts):
            raise ValueError("DC voltage must be finite")


@dataclass(frozen=True, slots=True)
class PulseVoltage:
    """A periodic voltage that moves between low and high levels.

    ``delay_seconds`` is the first transition's start. ``rise_seconds`` and
    ``fall_seconds`` are transition durations. ``high_seconds`` is the time
    held high per cycle, and ``period_seconds`` is the full cycle duration.
    These values describe a stimulus; they are not simulator command strings.
    """

    low_volts: float
    high_volts: float
    delay_seconds: float
    rise_seconds: float
    fall_seconds: float
    high_seconds: float
    period_seconds: float

    def __post_init__(self) -> None:
        """Reject waveforms whose timings cannot fit in one period."""
        values = (
            self.low_volts,
            self.high_volts,
            self.delay_seconds,
            self.rise_seconds,
            self.fall_seconds,
            self.high_seconds,
            self.period_seconds,
        )
        if not all(math.isfinite(value) for value in values):
            raise ValueError("pulse values must be finite")
        if min(self.delay_seconds, self.rise_seconds, self.fall_seconds) < 0:
            raise ValueError("pulse delay and edge times cannot be negative")
        if self.high_seconds <= 0 or self.period_seconds <= 0:
            raise ValueError("pulse high time and period must be positive")
        if (
            self.rise_seconds + self.high_seconds + self.fall_seconds
            > self.period_seconds
        ):
            raise ValueError("pulse transitions and high time exceed the period")


type VoltageWaveform = DcVoltage | PulseVoltage


@dataclass(frozen=True, slots=True)
class VoltageSource:
    """Drive a chosen voltage between two named circuit nets.

    The positive and negative nets are actual intended board nets. The SPICE
    converter attaches an ideal source between them in the simulated circuit;
    declaring a source does not add a physical board component. An ideal source
    has no output resistance or current limit, so it may be more capable than a
    real supply.
    """

    name: str
    positive_net: Net
    negative_net: Net
    waveform: VoltageWaveform
    ac_magnitude_volts: float | None = None

    def __post_init__(self) -> None:
        """Keep a source identifiable and connected across two distinct nets."""
        if not self.name.strip():
            raise ValueError("voltage source needs a name")
        if not isinstance(cast(object, self.positive_net), Net) or not isinstance(
            cast(object, self.negative_net), Net
        ):
            raise ValueError("voltage source nets must be Net enum members")
        if self.positive_net == self.negative_net:
            raise ValueError("voltage source terminals must be on different nets")
        if self.ac_magnitude_volts is not None and (
            not math.isfinite(self.ac_magnitude_volts) or self.ac_magnitude_volts <= 0
        ):
            raise ValueError("AC magnitude must be finite and positive")


@dataclass(frozen=True, slots=True)
class CurrentSource:
    """Force a constant current from one named net toward another.

    Current is in amperes; a negative value reverses the stated direction.
    This is a simulation stimulus, not a purchased component on the board.
    """

    name: str
    from_net: Net
    to_net: Net
    amperes: float

    def __post_init__(self) -> None:
        """Reject ambiguous or nonnumeric current injection."""
        if not self.name.strip():
            raise ValueError("current source needs a name")
        if not isinstance(cast(object, self.from_net), Net) or not isinstance(
            cast(object, self.to_net), Net
        ):
            raise ValueError("current source nets must be Net enum members")
        if self.from_net == self.to_net or not math.isfinite(self.amperes):
            raise ValueError("current source needs different nets and finite current")


type Source = VoltageSource | CurrentSource
