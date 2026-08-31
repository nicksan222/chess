"""MCP23017 I2C port expander in a hand-solderable PDIP-28 package.

Sixteen general-purpose pins read sixteen reed switches directly, so the board
needs no matrix scanning and no ghosting diodes. Every square input sits on the
left of the symbol and the bus, supply, address and interrupt pins on the right.
"""

from __future__ import annotations

from schemdraw import elements as elm

from .base import BY_PIN_NUMBER, Component, integrated_circuit

# Datasheet pin numbers for the sixteen port pins, port A first.
PORT_A_PINS = ("21", "22", "23", "24", "25", "26", "27", "28")
PORT_B_PINS = ("1", "2", "3", "4", "5", "6", "7", "8")
PORT_PINS = PORT_A_PINS + PORT_B_PINS

VDD_PIN = "9"
VSS_PIN = "10"
SCL_PIN = "12"
SDA_PIN = "13"
ADDRESS_PINS = ("15", "16", "17")
RESET_PIN = "18"
INTB_PIN = "19"
INTA_PIN = "20"
UNUSED_PINS = ("11", "14")

PIN_NAMES = {
    VDD_PIN: "VDD",
    VSS_PIN: "VSS",
    "11": "NC",
    SCL_PIN: "SCL",
    SDA_PIN: "SDA",
    "14": "NC",
    "15": "A0",
    "16": "A1",
    "17": "A2",
    RESET_PIN: "RESET",
    INTB_PIN: "INTB",
    INTA_PIN: "INTA",
}
PIN_NAMES.update(
    {pin: f"GPA{index}" for index, pin in enumerate(PORT_A_PINS)}
)
PIN_NAMES.update(
    {pin: f"GPB{index}" for index, pin in enumerate(PORT_B_PINS)}
)

RIGHT_PINS = (
    VDD_PIN,
    VSS_PIN,
    SCL_PIN,
    SDA_PIN,
    *ADDRESS_PINS,
    RESET_PIN,
    INTA_PIN,
    INTB_PIN,
    *UNUSED_PINS,
)


def _build() -> elm.Ic:
    left = [
        elm.IcPin(name=PIN_NAMES[pin], pin=pin, side="left", anchorname=pin)
        for pin in PORT_PINS
    ]
    right = [
        elm.IcPin(name=PIN_NAMES[pin], pin=pin, side="right", anchorname=pin)
        for pin in RIGHT_PINS
    ]
    # Every port pin carries a stub and a net flag, so the rows need more
    # clearance than the symbol body alone would suggest.
    return integrated_circuit(left + right, "MCP23017", pinspacing=1.9)


I2C_EXPANDER = Component(
    lib="MCP23017",
    value="MCP23017-E/SP",
    description="16-bit I2C port expander, one per board quadrant",
    package="PDIP-28",
    build=_build,
    pins=BY_PIN_NUMBER,
)
