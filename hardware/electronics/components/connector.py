"""Shared drawing for pin headers, so every connector looks the same.

A header is a body with named pins like an integrated circuit, which is what
lets the netlist name each contact instead of leaving a reader to count rows.
"""

from __future__ import annotations

from schemdraw import elements as elm

from .base import BY_PIN_NUMBER, Component, integrated_circuit


def pin_header(
    *,
    lib: str,
    value: str,
    description: str,
    package: str,
    label: str,
    left: dict[str, str],
    right: dict[str, str] | None = None,
    pinspacing: float = 1.9,
) -> Component:
    """A connector symbol whose pins are numbered as the datasheet numbers them.

    `left` and `right` map pin number to pin name. Splitting a long header
    across both sides keeps a forty-pin socket from running off the sheet.
    """
    right_pins = right or {}

    def build() -> elm.Ic:
        pins = [
            elm.IcPin(name=name, pin=number, side="left", anchorname=number)
            for number, name in left.items()
        ]
        pins += [
            elm.IcPin(name=name, pin=number, side="right", anchorname=number)
            for number, name in right_pins.items()
        ]
        return integrated_circuit(pins, label, pinspacing=pinspacing)

    return Component(
        lib=lib,
        value=value,
        description=description,
        package=package,
        build=build,
        pins=BY_PIN_NUMBER,
    )
