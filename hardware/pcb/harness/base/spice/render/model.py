"""Translate supported electrical device models into real SPICE element rows."""

from __future__ import annotations

import re

from ...net import Net
from ..model import SpiceModel
from .nodes import NodeMap
from .number import spice_number


def render_model(
    reference: str, model: SpiceModel, nets: tuple[Net, ...], nodes: NodeMap
) -> str:
    """Render one component model, or reject a kind with no converter.

    Terminal order is the order stated by ``SpiceModel``. At present the
    built-in converter handles only the device kinds listed below. Other model
    keys need explicit converters so a new part is never silently absent from a
    circuit. This method never evaluates raw text supplied by a component.
    """
    if len(nets) != len(model.terminals):
        raise ValueError(f"{reference}: model terminal/net count differs")
    if model.key in {"resistor", "capacitor", "diode", "button_static"}:
        if len(nets) != 2:
            raise ValueError(f"{model.key} model needs two terminals")
        prefix = {
            "resistor": "R",
            "capacitor": "C",
            "diode": "D",
            "button_static": "SW",
        }[model.key]
        if not re.fullmatch(rf"{prefix}[A-Za-z0-9_]+", reference):
            raise ValueError(f"{model.key} reference must start with {prefix}")
        first, second = (nodes.node(net) for net in nets)
        if model.key == "resistor":
            resistance = _parameter(model, "resistance", "ohm", positive=True)
            return f"{reference} {first} {second} {spice_number(resistance)}"
        if model.key == "capacitor":
            capacitance = _parameter(model, "capacitance", "farad", positive=True)
            return f"{reference} {first} {second} {spice_number(capacitance)}"
        if model.key == "button_static":
            resistance = _parameter(model, "contact_resistance", "ohm", positive=True)
            return f"Rcontact_{reference} {first} {second} {spice_number(resistance)}"
        saturation = _parameter(model, "saturation_current", "ampere", positive=True)
        ideality = _parameter(model, "ideality_factor", "ratio", positive=True)
        series = _parameter(model, "series_resistance", "ohm", positive=False)
        return (
            f"{reference} {first} {second} D_{reference}\n"
            f".model D_{reference} D(Is={spice_number(saturation)} "
            f"N={spice_number(ideality)} Rs={spice_number(series)})"
        )
    raise ValueError(f"unsupported model: {model.key}")


def _parameter(model: SpiceModel, name: str, unit: str, *, positive: bool) -> float:
    """Return one validated parameter; reject extras and mismatched units."""
    expected_count = 3 if model.key == "diode" else 1
    if len(model.parameters) != expected_count:
        raise ValueError(f"{model.key} model needs {expected_count} parameters")
    matches = [value for value in model.parameters if value.name == name]
    if len(matches) != 1 or matches[0].unit != unit:
        raise ValueError(f"{model.key} needs {name} in {unit}")
    value = matches[0].value
    outside_range = value <= 0 if positive else value < 0
    if outside_range:
        qualifier = "positive" if positive else "nonnegative"
        raise ValueError(f"{model.key} needs {qualifier} {name} in {unit}")
    return value
