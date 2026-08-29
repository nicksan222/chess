"""Battery pack, protection, and 5 V regulator."""

from __future__ import annotations

from core.canvas import Schematic
from components import (
    BATTERY,
    BUCK_5V_5A,
    ELECTROLYTIC_8X10,
    ELECTROLYTIC_10X10,
    FUSE,
    SWITCH,
    TESTPOINT_LOOP,
    TVS,
    capacitor,
    resistor,
    testpoint,
)


def add_power(sch: Schematic, *, origin_x: float = 8.0, rail_y: float = 30.0) -> None:
    """Battery to 5 V, drawn left to right along one rail."""
    enable_y = rail_y + 8.0
    sch.place(BATTERY, "BT1", origin_x, rail_y)
    sch.place(FUSE, "F1", origin_x + 9.0, rail_y)
    sch.place(SWITCH, "SW1", origin_x + 18.0, rail_y)
    # Shunt parts hang off the rail they protect, in line with it.
    sch.place(TVS, "D1", origin_x + 25.0, rail_y - 3.0)
    sch.place(
        capacitor(ELECTROLYTIC_8X10, "220uF 16V", "Regulator input bulk capacitor"),
        "C1",
        origin_x + 30.0,
        rail_y,
    )
    sch.place(
        resistor("100k", "Regulator enable pull-up"), "R1", origin_x + 30.0, enable_y
    )
    sch.place(BUCK_5V_5A, "U1", origin_x + 40.0, rail_y)
    sch.place(
        capacitor(ELECTROLYTIC_10X10, "1000uF 10V", "LED rail bulk capacitor"),
        "C2",
        origin_x + 50.0,
        rail_y,
    )
    sch.place(
        testpoint(TESTPOINT_LOOP, "+5V", "5 V test point"), "TP1", origin_x + 56.0, rail_y
    )
    sch.place(
        testpoint(TESTPOINT_LOOP, "GND", "Ground test point"),
        "TP2",
        origin_x + 56.0,
        rail_y - 7.0,
    )

    sch.hv(*sch.pin("BT1", "1"), *sch.pin("F1", "1"))
    sch.hv(*sch.pin("F1", "2"), *sch.pin("SW1", "1"))
    sch.hv(*sch.pin("SW1", "2"), *sch.pin("U1", "1"))
    sch.tap(*sch.pin("D1", "1"))
    sch.tap(*sch.pin("C1", "1"))
    # Enable is pulled to the switched battery rail up and over the regulator.
    sch.vh(*sch.pin("U1", "4"), *sch.pin("R1", "2"))
    # The output rail carries its own bulk capacitance and test point.
    sch.hv(*sch.pin("U1", "3"), *sch.pin("TP1", "1"))
    sch.tap(*sch.pin("C2", "1"))

    for ref, pin, net in (
        ("BT1", "1", "BATT_RAW"),
        ("F1", "2", "BATT_FUSED"),
        ("SW1", "2", "BATT_SW"),
        ("R1", "1", "BATT_SW"),
        ("U1", "3", "+5V"),
        ("BT1", "2", "GND"),
        ("U1", "2", "GND"),
        ("C1", "2", "GND"),
        ("C2", "2", "GND"),
        ("D1", "2", "GND"),
        ("TP2", "1", "GND"),
    ):
        sch.label_pin(net, ref, pin)
