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
    if model.key in {
        "open_drain_sensor",
        "input_pullup_bank",
        "button_contact",
    } and not re.fullmatch(r"[A-Za-z][A-Za-z0-9_]*", reference):
        raise ValueError("unsafe component model reference")
    if model.key == "button_contact":
        if len(nets) != 2:
            raise ValueError("button contact needs two terminals")
        first, second = (nodes.node(net) for net in nets)
        resistance = _parameter(model, "on_resistance", "ohm", positive=True)
        return (
            f"Scontact_{reference} {first} {second} state_{reference} 0 SW_{reference}\n"
            f".model SW_{reference} SW(Ron={spice_number(resistance)} Roff=1e12 Vt=0.5 Vh=0)"
        )
    if model.key == "open_drain_sensor":
        if len(nets) != 3:
            raise ValueError(
                "open-drain sensor needs output, supply and ground terminals"
            )
        output, supply, ground = (nodes.node(net) for net in nets)
        resistance = _parameter(model, "on_resistance", "ohm", positive=True)
        leakage = _parameter(model, "off_leakage", "ampere", positive=False)
        return (
            f"Soutput_{reference} {output} {ground} state_{reference} 0 SW_{reference}\n"
            f".model SW_{reference} SW(Ron={spice_number(resistance)} Roff=1e12 Vt=0.5 Vh=0)\n"
            f"Ileak_{reference} {output} {ground} {spice_number(leakage)}\n"
            f"Rbias_{reference} {supply} {ground} 1e12"
        )
    if model.key == "input_pullup_bank":
        if len(nets) != 10:
            raise ValueError(
                "input bank needs supply, ground and eight input terminals"
            )
        supply, ground, *inputs = (nodes.node(net) for net in nets)
        resistance = _parameter(model, "pullup_resistance", "ohm", positive=True)
        leakage = _parameter(model, "input_leakage", "ampere", positive=False)
        return "\n".join(
            row
            for index, pin in enumerate(inputs)
            for row in (
                f"Rpull_{reference}_{index} {pin} {supply} {spice_number(resistance)}",
                f"Ileak_{reference}_{index} {pin} {ground} {spice_number(leakage)}",
            )
        )
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
    expected_count = {"diode": 3, "open_drain_sensor": 2, "input_pullup_bank": 2}.get(
        model.key, 1
    )
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
