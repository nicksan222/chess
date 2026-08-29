"""Pico 2 W, LED level shifter, and battery ADC."""

from __future__ import annotations

from core.canvas import Schematic
from components import (
    AHCT125,
    CERAMIC_0603,
    CERAMIC_0805,
    PICO_2_W,
    TESTPOINT_PAD,
    capacitor,
    resistor,
    testpoint,
)
from core.names import (
    BAT_ADC_PIN,
    COL_PINS,
    LED_DATA_PIN,
    PICO_3V3_PIN,
    PICO_5V_PIN,
    PICO_GND_PINS,
    PICO_UNUSED_PINS,
    ROW_PINS,
)


def add_controller(sch: Schematic) -> None:
    # The Pico is tall and narrow, so the supporting circuits stack alongside it
    # rather than trailing off to one side.
    sch.place(PICO_2_W, "U2", 172.0, 46.0)
    sch.place(resistor("100k 1%", "Battery divider upper resistor"), "R3", 196.0, 74.0)
    sch.place(resistor("39k 1%", "Battery divider lower resistor"), "R4", 206.0, 74.0)
    sch.place(resistor("10k", "ADC fault-current limiting resistor"), "R5", 201.0, 68.0)
    sch.place(
        capacitor(CERAMIC_0603, "100nF", "Battery ADC low-pass capacitor"),
        "C5",
        216.0,
        74.0,
    )
    sch.place(
        capacitor(CERAMIC_0805, "10uF", "Pico local supply capacitor"),
        "C3",
        196.0,
        58.0,
    )
    sch.place(AHCT125, "U67", 196.0, 42.0)
    sch.place(resistor("330R", "LED data source termination"), "R2", 208.0, 42.0)
    sch.place(
        testpoint(TESTPOINT_PAD, "LED_DATA_5V", "Buffered LED data test point"),
        "TP3",
        218.0,
        42.0,
    )
    sch.place(
        capacitor(CERAMIC_0603, "100nF", "Level shifter decoupling"),
        "C4",
        206.0,
        34.0,
    )

    for ref, pin, net in (
        ("U2", PICO_5V_PIN, "+5V"),
        ("U2", PICO_3V3_PIN, "+3V3"),
        ("C3", "1", "+5V"),
        ("C3", "2", "GND"),
        ("U67", "5", "+5V"),
        ("C4", "1", "+5V"),
        ("C4", "2", "GND"),
    ):
        sch.label_pin(net, ref, pin)
    sch.label_pin("GND", "U67", "1")
    sch.label_pin("GND", "U67", "3")
    for gnd_pin in PICO_GND_PINS:
        sch.label_pin("GND", "U2", gnd_pin)

    sch.label_pin("BATT_SW", "R3", "1")
    sch.label_pin("GND", "R4", "2")
    sch.wire(*sch.pin("R3", "2"), *sch.pin("R4", "1"))
    divider_x = sch.pin("R5", "1")[0]
    sch.wire(divider_x, sch.pin("R5", "1")[1], divider_x, 74.0)
    sch.tap(divider_x, 74.0)
    # BAT_ADC reaches the Pico by name: a drawn wire would double back over the
    # divider on the same horizontal as R5 and read as a short across it.
    sch.label_pin("BAT_ADC", "R5", "2")
    sch.label_pin("BAT_ADC", "C5", "1")
    sch.label_pin("GND", "C5", "2")
    sch.label_pin("BAT_ADC", "U2", BAT_ADC_PIN)

    # The Pico sits far below the shifter, so a drawn GP0 wire would sweep across
    # the whole block; the net label carries the same connection without the sweep.
    sch.label_pin("LED_DATA_3V3", "U2", LED_DATA_PIN)
    sch.label_pin("LED_DATA_3V3", "U67", "2")
    yout = sch.pin("U67", "4")
    r2in = sch.pin("R2", "1")
    sch.wire(*yout, r2in[0], yout[1])
    sch.wire(r2in[0], yout[1], *r2in)
    sch.label_pin("LED_DATA_CHAIN", "R2", "2")
    sch.hv(*sch.pin("R2", "2"), *sch.pin("TP3", "1"))

    for number in PICO_UNUSED_PINS:
        sch.nc(*sch.pin("U2", number))

    for rank, pin in enumerate(ROW_PINS):
        sch.label_pin(f"ROW_{rank}", "U2", pin)
    for file_index, pin in enumerate(COL_PINS):
        sch.label_pin(f"COL_{file_index}", "U2", pin)

    sch.note(
        "GP0 LED data, GP1-GP8 rows, GP9-GP16 columns, GP26 battery ADC",
        160.0,
        24.0,
    )
