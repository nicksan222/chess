"""Shared MOSFET pin semantics for the LED rail switch (S6, interface H5).

Vishay Si4403DDY SO-8 (S17-0318-Rev A p1 top view): 1-3 source, 4 gate, 5-8 drain;
the three sources and four drains are each one terminal inside the package.
onsemi BSS138LT1G SOT-23 STYLE 21 (BSS138LT1/D Rev 15): 1 gate, 2 source, 3 drain.
TI SN74LVC1G97 DBV (SCES416N pin functions): 1 In1, 2 GND, 3 In0, 4 Y, 5 VCC, 6 In2;
Table 1: Y follows In1 while In2 is low and In0 while In2 is high, so with In0
tied high it is In2 OR In1.
"""

from enum import StrEnum

from shared.components import LED_ENABLE_GATE, LED_SWITCH, LED_SWITCH_DRIVER
from shared.electronics.base import ElectronicComponent


class PowerMosfetPin(StrEnum):
    """Si4403DDY SO-8 pins: three sources, the gate, and four drains tied together."""

    SOURCE_1 = "1"
    SOURCE_2 = "2"
    SOURCE_3 = "3"
    GATE = "4"
    DRAIN_5 = "5"
    DRAIN_6 = "6"
    DRAIN_7 = "7"
    DRAIN_8 = "8"


SOURCE_PINS = (
    PowerMosfetPin.SOURCE_1,
    PowerMosfetPin.SOURCE_2,
    PowerMosfetPin.SOURCE_3,
)
DRAIN_PINS = (
    PowerMosfetPin.DRAIN_5,
    PowerMosfetPin.DRAIN_6,
    PowerMosfetPin.DRAIN_7,
    PowerMosfetPin.DRAIN_8,
)


class PowerMosfetComponent(ElectronicComponent[PowerMosfetPin]):
    """Typed model of the LED rail switch Q1 (P-channel)."""

    pin_type = PowerMosfetPin
    specs = (LED_SWITCH,)


class SmallMosfetPin(StrEnum):
    """BSS138 SOT-23 pins: gate, source, drain."""

    GATE = "1"
    SOURCE = "2"
    DRAIN = "3"


class SmallMosfetComponent(ElectronicComponent[SmallMosfetPin]):
    """Typed model of the LED switch driver Q2 (N-channel)."""

    pin_type = SmallMosfetPin
    specs = (LED_SWITCH_DRIVER,)


class LogicGatePin(StrEnum):
    """SN74LVC1G97 SOT-23-6 pins: three inputs (In0, In1, In2), output Y, supply and ground."""

    INPUT_1 = "1"
    GROUND = "2"
    INPUT_0 = "3"
    OUTPUT = "4"
    SUPPLY = "5"
    INPUT_2 = "6"


class LogicGateComponent(ElectronicComponent[LogicGatePin]):
    """Typed model of the buffer-enable gate U75."""

    pin_type = LogicGatePin
    specs = (LED_ENABLE_GATE,)
