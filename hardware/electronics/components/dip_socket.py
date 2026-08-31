"""DIP sockets, so no integrated circuit ever sees a soldering iron.

A socket carries no net of its own: it sits between a chip and the board. It is
drawn beside the chip it holds, without pins, purely so the bill of materials
lists the hardware an assembler still has to buy. Sockets also make a fried chip
a thirty-second swap rather than surface-mount rework on a 320 mm board.
"""

from __future__ import annotations

from schemdraw import elements as elm

from .base import BY_PIN_NUMBER, Component, integrated_circuit


def _socket(ways: int):
    def build() -> elm.Ic:
        return integrated_circuit([], f"{ways}-pin DIP socket")

    return build


def dip_socket(ways: int) -> Component:
    return Component(
        lib="DIP_SOCKET",
        value=f"DIP-{ways} socket",
        description="Turned-pin socket; the chip drops in after assembly",
        package=f"DIP-{ways}",
        build=_socket(ways),
        pins=BY_PIN_NUMBER,
    )


SOCKET_DIP14 = dip_socket(14)
SOCKET_DIP28 = dip_socket(28)
