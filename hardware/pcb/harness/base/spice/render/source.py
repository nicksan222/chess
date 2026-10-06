"""Translate physical-unit stimulus declarations into SPICE source rows."""

from __future__ import annotations

import re
from typing import cast

from ..source import CurrentSource, DcVoltage, PulseVoltage, Source, VoltageSource
from .nodes import NodeMap
from .number import spice_number


def render_source(source: Source, nodes: NodeMap) -> str:
    """Render one independent voltage or current stimulus.

    SPICE's first letter identifies the electrical element kind: ``V`` is an
    ideal voltage source and ``I`` an ideal current source. This converter
    enforces that rule and uses ``NodeMap`` for safe node names.
    """
    if isinstance(source, VoltageSource):
        if not re.fullmatch(r"V[A-Za-z0-9_]+", source.name):
            raise ValueError("voltage source names must start with V")
        positive = nodes.node(source.positive_net)
        negative = nodes.node(source.negative_net)
        waveform = source.waveform
        if isinstance(waveform, DcVoltage):
            value = f"DC {spice_number(waveform.volts)}"
            if source.ac_magnitude_volts is not None:
                value += f" AC {spice_number(source.ac_magnitude_volts)}"
        elif isinstance(cast(object, waveform), PulseVoltage):
            if source.ac_magnitude_volts is not None:
                raise ValueError("AC excitation requires a DC waveform")
            values = (
                waveform.low_volts,
                waveform.high_volts,
                waveform.delay_seconds,
                waveform.rise_seconds,
                waveform.fall_seconds,
                waveform.high_seconds,
                waveform.period_seconds,
            )
            value = "PULSE(" + " ".join(spice_number(number) for number in values) + ")"
        else:
            raise ValueError(f"{source.name}: unsupported voltage waveform")
        return f"{source.name} {positive} {negative} {value}"
    if isinstance(cast(object, source), CurrentSource):
        if not re.fullmatch(r"I[A-Za-z0-9_]+", source.name):
            raise ValueError("current source names must start with I")
        return (
            f"{source.name} {nodes.node(source.from_net)} "
            f"{nodes.node(source.to_net)} DC {spice_number(source.amperes)}"
        )
    raise ValueError("unsupported source kind")
