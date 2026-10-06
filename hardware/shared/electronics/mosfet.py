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
