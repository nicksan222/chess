"""Translate typed operating-point, time and frequency analyses."""

from __future__ import annotations

from typing import cast

from ..analysis import AcSweep, Analysis, OperatingPoint, Transient
from .number import spice_number


def render_analysis(analysis: Analysis) -> str:
    """Return one ngspice analysis directive from physical-unit settings."""
    if isinstance(analysis, OperatingPoint):
        return ".op"
    if isinstance(analysis, Transient):
        return (
            f".tran {spice_number(analysis.max_step_seconds)} "
            f"{spice_number(analysis.duration_seconds)}"
        )
    if isinstance(cast(object, analysis), AcSweep):
        return (
            f".ac dec {analysis.points_per_decade} "
            f"{spice_number(analysis.start_hz)} {spice_number(analysis.stop_hz)}"
        )
    raise ValueError("unsupported analysis kind")
