"""LED rail switch (S6, user decision D1, interface H5): LED_5V off until the Pi asks.

The Pi's LED_EN (BCM26, header pin 37, reset pull-down) drives Q2 through R13; R14
holds Q2's gate low while the Pi boots, resets or is absent. Q2 pulls LED_EN_N low
against R15: LED_EN_N gates Q1 through R16 (with C145 gate-to-drain, a Miller ramp
of about 1.5 ms). S6b (H6): U75 (SN74LVC1G97 as a Schmitt OR) makes LED_OE_N =
Q1 gate OR LED_EN_N, the AHCT125 1OE/2OE: the buffer stays Hi-Z until Q1's gate has
left its Miller plateau (LED_5V fully up) and goes Hi-Z within a microsecond of
LED_EN falling, before LED_5V drops, so U5 never drives the chain above its VDD.
"""

from __future__ import annotations

import pcbnew

from pcb.definition.assemblies.power import add_strip
from pcb.definition.native import connect
from pcb.definition.parts import catalog as parts
from pcb.definition.parts.part import PcbPart
from shared import electronics as p
from shared import wiring
from shared.electronics.mosfet import DRAIN_PINS, SOURCE_PINS

# Assembly tag stored on the footprints; the schematic groups them on the controls sheet.
ASSEMBLY = "led-switch"
# Q1 Q2 R13 R14 R15 R16 C145 U75 C146
ASSEMBLY_PART_COUNT = 9
# References of the power switch (P-channel) and its driver (N-channel inverter).
SWITCH, DRIVER = "Q1", "Q2"


def add_led_switch(
    board: pcbnew.BOARD,
    host: p.RaspberryPiHeaderComponent,
    buffer: p.Ahct125Component,
) -> None:
    """Place the switch parts and wire them to the Pi pin and the AHCT125 enables.

    `host` supplies the LED_EN pin and `buffer` the two output-enable pins that follow
    U75. Nets: LED_EN -> R13 -> Q2 gate; LED_EN_N (Q2 drain, R15 pull-up) -> R16 -> Q1 gate
    (LED_SW_GATE) and U75; U75 output LED_OE_N -> U5 OE pins; Q1 source on +5V, Q1 drain
    on LED_5V. Every pin of every part is connected here.
    """
    switch = add_strip(board, parts.LED_SWITCH_PART, SWITCH, assembly=ASSEMBLY)
    driver = add_strip(board, parts.LED_SWITCH_DRIVER_PART, DRIVER, assembly=ASSEMBLY)

    # All resistors share the same placement path; only reference, part and purpose differ.
    def resistor(
        part: PcbPart[p.ResistorComponent], reference: str, purpose: str
    ) -> p.ResistorComponent:
        return add_strip(board, part, reference, assembly=ASSEMBLY, purpose=purpose)

    series = resistor(parts.RES_1K_PART, "R13", "LED_EN series to Q2 gate")
    hold = resistor(parts.RES_100K_PART, "R14", "Q2 gate pull-down (LED rail off)")
    pull_up = resistor(parts.RES_10K_PART, "R15", "LED_EN_N pull-up")
    gate = resistor(parts.RES_100K_PART, "R16", "Q1 gate drive (turn-on ramp)")
    miller = add_strip(
        board,
        parts.CAP_10N_PART,
        "C145",
        assembly=ASSEMBLY,
        purpose="Q1 gate-to-drain ramp capacitor",
    )
    gate_or = add_strip(board, parts.LED_ENABLE_GATE_PART, "U75", assembly=ASSEMBLY)
    gate_or_bypass = add_strip(
        board,
        parts.CAP_100N_PART,
        "C146",
        assembly=ASSEMBLY,
        purpose="U75 decoupling capacitor",
    )
    a, b = p.ResistorPin.TERMINAL_A, p.ResistorPin.TERMINAL_B
    connect(
        board,
        wiring.LED_ENABLE_NET,
        host.pin(p.RaspberryPiHeaderPin.LED_EN_GPIO26),
        series.pin(a),
    )
    connect(
        board,
        "LED_EN_GATE",
        series.pin(b),
        hold.pin(a),
        driver.pin(p.SmallMosfetPin.GATE),
    )
