"""Reusable per-square cells: reed+diode, LED+decoupling, column pull-up."""

from __future__ import annotations

from core.canvas import Schematic
from components import CERAMIC_0603, DIODE, REED, WS2812B, capacitor, resistor


def add_reed_cell(
    sch: Schematic,
    *,
    square_name: str,
    reed_ref: str,
    diode_ref: str,
    col_x: float,
    y: float,
    row_net: str,
    reed_offset: float = 1.2,
    diode_offset: float = 5.2,
    col_stub: float = 0.9,
) -> None:
    reed_x = col_x + reed_offset
    diode_x = col_x + diode_offset
    bus_x = col_x - col_stub
    sch.place(REED, reed_ref, reed_x, y, {"Square": square_name}, {"Square"})
    sch.place(DIODE, diode_ref, diode_x, y, {"Square": square_name})
    sch.hv(*sch.pin(reed_ref, "2"), *sch.pin(diode_ref, "2"))
    sch.wire(*sch.pin(reed_ref, "1"), bus_x, y)
    sch.tap(bus_x, y)
    sch.label_pin(row_net, diode_ref, "1")


def add_column_pullup(
    sch: Schematic,
    *,
    ref: str,
    col_x: float,
    y: float,
    col_net: str,
    col_stub: float = 0.9,
    pull_offset: float = 4.2,
    description: str | None = None,
) -> None:
    sch.place(
        resistor("10k", description or f"Column pull-up for {col_net}"),
        ref,
        col_x - pull_offset,
        y,
    )
    sch.label_pin("+3V3", ref, "1")
    sch.wire(*sch.pin(ref, "2"), col_x - col_stub, y)
    sch.label(col_net, col_x - col_stub, y)


def add_led_cell(
    sch: Schematic,
    *,
    square_name: str,
    chain_index: int,
    led_ref: str,
    cap_ref: str,
    x: float,
    y: float,
    cap_dx: float = -6.5,
    cap_dy: float = 1.0,
) -> None:
    sch.place(
        WS2812B,
        led_ref,
        x,
        y,
        {"Square": square_name, "ChainIndex": str(chain_index)},
        {"Square"},
    )
    # Rail labels rather than wires: routing the cap back to the LED pins drags
    # two wires straight through the reference and value text of both parts.
    # Beside the LED, not beneath it, so the cell stays short enough to tile.
    sch.place(
        capacitor(CERAMIC_0603, "100nF", "Local LED decoupling capacitor"),
        cap_ref,
        x + cap_dx,
        y + cap_dy,
        {"Square": square_name},
    )
    sch.label_pin("+5V", led_ref, "1")
    sch.label_pin("GND", led_ref, "3")
    sch.label_pin("+5V", cap_ref, "1")
    sch.label_pin("GND", cap_ref, "2")
