"""Translate component-owned proof requests into ngspice measurement commands."""

from __future__ import annotations

import re
from collections.abc import Mapping
from typing import cast

from ...connections import Endpoint
from ...net import Net
from ..analysis import AcSweep, Analysis, OperatingPoint, Transient
from ..measurement import (
    CurrentThrough,
    Observation,
    SpiceRequirement,
    VoltageAt,
    VoltageBetween,
)
from .nodes import NodeMap
from .number import spice_number


def render_measurement(
    name: str,
    requirement: SpiceRequirement,
    analysis: Analysis,
    nets: Mapping[Endpoint, Net],
    nodes: NodeMap,
) -> str:
    """Render one measured scalar from a typed endpoint or source reference.

    Operating point measurements become control-language ``let`` expressions.
    Transient and AC measurements become ``meas`` commands. The caller checks
    the result against ``requirement.allowed`` after this command executes.
    A source current follows ngspice's current direction for that source.
    """
    if not re.fullmatch(r"result_[a-z0-9_]+", name):
        raise ValueError("measurement result name must be safe and start result_")

    def net_of(endpoint: Endpoint) -> str:
        try:
            return nodes.node(nets[endpoint])
        except KeyError as error:
            raise ValueError(
                f"unknown endpoint: {endpoint.reference}/{endpoint.pin}"
            ) from error

    measurement = requirement.measurement
    if isinstance(measurement, VoltageAt):
        # SPICE reports node voltage relative to node 0, which NodeMap assigns
        # to the scenario's declared ground net.
        expression = f"v({net_of(measurement.pin)})"
    elif isinstance(measurement, VoltageBetween):
        expression = f"v({net_of(measurement.positive)},{net_of(measurement.negative)})"
    elif isinstance(cast(object, measurement), CurrentThrough):
        if not re.fullmatch(r"V[A-Za-z0-9_]+", measurement.source):
            raise ValueError("current measurement needs a voltage source name")
        expression = f"i({measurement.source})"
    else:
        raise ValueError("unsupported measurement kind")
    observation = requirement.observation
    if isinstance(analysis, OperatingPoint):
        # An operating point has a single solved value, not a time or frequency
        # series from which a minimum, maximum, or final sample could be chosen.
        if observation is not Observation.SINGLE:
            raise ValueError("operating point requires SINGLE observation")
        return f"let {name} = {expression}"
    if isinstance(analysis, Transient):
        if observation is Observation.FINAL:
            return (
                f"meas tran {name} FIND {expression} "
                f"AT={spice_number(analysis.duration_seconds)}"
            )
        if observation in (Observation.MINIMUM, Observation.MAXIMUM):
            operation = "MIN" if observation is Observation.MINIMUM else "MAX"
            return f"meas tran {name} {operation} {expression}"
        raise ValueError("transient requires FINAL, MINIMUM or MAXIMUM observation")
    if isinstance(cast(object, analysis), AcSweep):
        if observation in (Observation.MINIMUM, Observation.MAXIMUM):
            operation = "MIN" if observation is Observation.MINIMUM else "MAX"
            magnitude = f"magnitude_{name}"
            return (
                f"let {magnitude} = mag({expression})\n"
                f"meas ac {name} {operation} {magnitude}"
            )
        raise ValueError("AC sweep requires MINIMUM or MAXIMUM observation")
    raise ValueError("unsupported analysis kind")
