"""Shared shape of a single component definition.

Every module in this package describes exactly one physical part: what it is
called in a bill of materials, and how Schemdraw should draw it.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, replace

from schemdraw import elements as elm

# Datasheet pin number -> Schemdraw anchor name.
TWO_TERMINAL = {"1": "start", "2": "end"}
POLARIZED = {"1": "end", "2": "start"}
SINGLE = {"1": "center"}
# Integrated circuits publish their pin numbers as anchors already.
BY_PIN_NUMBER: dict[str, str] = {}


@dataclass(frozen=True)
class Component:
    lib: str
    value: str
    description: str
    package: str
    build: Callable[[], elm.Element]
    pins: dict[str, str]
    # What to call this on a purchase order when the drawn value is a net name
    # rather than a part, as it is for a test point.
    part: str = ""

    @property
    def ordering(self) -> str:
        return self.part or self.value or self.lib

    def variant(self, value: str, description: str) -> Component:
        return replace(self, value=value, description=description)


PIN_NAME_FONT = 8
PIN_NUMBER_FONT = 7


def integrated_circuit(pins: list[elm.IcPin], label: str, **kwargs) -> elm.Ic:
    """An IC body with its part name offset clear of any bottom pin.

    The explicit `right()` matters: Schemdraw carries the previous element's
    direction forward, so without it a body placed after a vertical capacitor
    comes out rotated and its pins land on the wrong sides.
    """
    sized = [
        replace(pin, lblsize=PIN_NAME_FONT, pinlblsize=PIN_NUMBER_FONT) for pin in pins
    ]
    return (
        elm.Ic(pins=sized, leadlen=0.6, edgepadH=0.3, edgepadW=0.6, **kwargs)
        .right()
        .label(label, loc="bottom", ofst=(1.6, -0.2), halign="left", fontsize=9)
    )
