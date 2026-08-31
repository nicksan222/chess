"""5 V input: jack, fuse, clamp, switch, bulk capacitance.

There is no regulator anywhere on this board. A 5 V brick feeds the rail
directly, and the 3.3 V the expanders need comes off the Pi's own header, so the
entire power section is six parts. What would have been a buck converter, an
inductor and a USB power-negotiation chip is simply absent.
"""

from __future__ import annotations

from core.canvas import Schematic
from components import (
    BARREL_JACK,
    ELECTROLYTIC_RADIAL,
    ELECTROLYTIC_SMALL,
    FUSE,
    SWITCH,
    TVS,
    capacitor,
    testpoint,
)


def add_power(sch: Schematic, *, origin_x: float = 8.0, rail_y: float = 30.0) -> None:
    """Jack to 5 V rail, drawn left to right along one line."""
    sch.place(BARREL_JACK, "J3", origin_x, rail_y)
    sch.place(FUSE, "F1", origin_x + 12.0, rail_y)
    sch.place(SWITCH, "SW13", origin_x + 22.0, rail_y)
    # Shunt parts hang off the rail they protect, in line with it.
    sch.place(TVS, "D1", origin_x + 31.0, rail_y - 4.0)
    sch.place(
        capacitor(ELECTROLYTIC_RADIAL, "1000uF 10V", "LED rail bulk capacitor"),
        "C1",
        origin_x + 38.0,
        rail_y,
    )
    sch.place(
        capacitor(ELECTROLYTIC_SMALL, "10uF 16V", "Rail decoupling capacitor"),
        "C2",
        origin_x + 44.0,
        rail_y,
    )
    sch.place(testpoint("+5V", "5 V test point"), "TP1", origin_x + 50.0, rail_y)
    sch.place(
        testpoint("GND", "Ground test point"), "TP2", origin_x + 50.0, rail_y - 8.0
    )

    sch.hv(*sch.pin("J3", "1"), *sch.pin("F1", "1"))
    sch.hv(*sch.pin("F1", "2"), *sch.pin("SW13", "1"))
    sch.hv(*sch.pin("SW13", "2"), *sch.pin("TP1", "1"))
    # The clamp stands below the rail, so it gets a drawn stub up to it rather
    # than a junction dot placed where the symbol happens to end.
    clamp_x, clamp_y = sch.pin("D1", "1")
    sch.wire(clamp_x, clamp_y, clamp_x, rail_y)
    sch.tap(clamp_x, rail_y)
    sch.tap(*sch.pin("C1", "1"))
    sch.tap(*sch.pin("C2", "1"))

    for ref, pin, net in (
        ("J3", "1", "DC_IN"),
        ("F1", "2", "DC_FUSED"),
        ("SW13", "2", "+5V"),
        ("J3", "2", "GND"),
        ("C1", "2", "GND"),
        ("C2", "2", "GND"),
        ("D1", "2", "GND"),
        ("TP2", "1", "GND"),
    ):
        sch.label_pin(net, ref, pin)

    sch.note(
        "5 V 5 A brick. No regulator on board; 3.3 V comes from the Pi header.",
        origin_x - 2.0,
        rail_y - 13.0,
    )
    sch.note(
        "Do not also power the Pi's micro-USB: two 5 V sources would fight.",
        origin_x - 2.0,
        rail_y - 16.0,
    )
