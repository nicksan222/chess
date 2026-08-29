"""Serpentine WS2812B chain built from per-square LED cells."""

from __future__ import annotations

from blocks.square import add_led_cell
from core.canvas import Schematic
from components import TESTPOINT_PAD, testpoint
from core.names import led_chain_order

# Horizontal lanes above a cell, clear of its supply symbol.
BYPASS_LANE = 5.0
TURN_LANE = 6.6


def add_led_chain(
    sch: Schematic,
    *,
    origin_x: float = 14.0,
    origin_y: float = 64.0,
    pitch_x: float = 17.0,
    pitch_y: float = 12.0,
    source_net: str = "LED_DATA_CHAIN",
) -> list[str]:
    chain = led_chain_order()
    led_refs: list[str] = []
    for index, (name, file_index, rank) in enumerate(chain):
        led = f"U{3 + index}"
        led_refs.append(led)
        add_led_cell(
            sch,
            square_name=name,
            chain_index=index + 1,
            led_ref=led,
            cap_ref=f"C{6 + index}",
            x=origin_x + file_index * pitch_x,
            y=origin_y + rank * pitch_y,
        )

    sch.label_pin(source_net, led_refs[0], "4")
    for index in range(len(led_refs) - 1):
        a = sch.pin(led_refs[index], "2")
        b = sch.pin(led_refs[index + 1], "4")
        if (index % 8) != 7 and a[0] < b[0]:
            sch.wire(*a, *b)
        elif (index % 8) != 7:
            # Odd ranks run right to left, so DOUT has to double back. Clear the
            # supply symbols standing above every cell before crossing.
            sch.wire(*a, a[0], a[1] + BYPASS_LANE)
            sch.wire(a[0], a[1] + BYPASS_LANE, b[0], b[1] + BYPASS_LANE)
            sch.wire(b[0], b[1] + BYPASS_LANE, *b)
        else:
            turn_y = a[1] + TURN_LANE
            sch.wire(*a, a[0] + 2.4, a[1])
            sch.wire(a[0] + 2.4, a[1], a[0] + 2.4, turn_y)
            sch.wire(a[0] + 2.4, turn_y, b[0] - 2.4, turn_y)
            sch.wire(b[0] - 2.4, turn_y, b[0] - 2.4, b[1])
            sch.wire(b[0] - 2.4, b[1], *b)

    last_dout = sch.pin(led_refs[-1], "2")
    sch.place(
        testpoint(TESTPOINT_PAD, "LED_DOUT_LAST", "End-of-chain LED data test point"),
        "TP4",
        last_dout[0] + 4.0,
        last_dout[1],
    )
    sch.hv(*last_dout, *sch.pin("TP4", "1"))
    sch.label_pin("LED_DOUT_LAST", "TP4", "1")
    sch.tap(*sch.pin("TP4", "1"))
    return led_refs
