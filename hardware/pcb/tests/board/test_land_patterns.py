"""Approved land patterns against hand-typed datasheet facts.

Every row below is copied by hand from the cited manufacturer document, not derived
from `shared.electronics` enums or `definition.parts` constructors. Pad centres,
copper sizes and drills use the datasheet's own top view: millimetres, package centre
origin, Y up. When a template is drawn in a frame rotated from the drawing (to keep
an existing board placement), `frame_rotation_deg` states that pure rotation; it
preserves chirality, so a mirrored or renumbered land still fails. `function` is the
repository's semantic name for the datasheet pin and `rail` the supply net that pin
must reach on the native board. Parts whose land could not be sourced are listed in
`UNVERIFIED` with the reason, never given invented dimensions.
"""

import math
import unittest
from dataclasses import dataclass
from itertools import pairwise
from typing import ClassVar

import pcbnew

from pcb.definition import board, native
from pcb.definition.parts.catalog import PCB_PARTS
from pcb.definition.parts.part import DrawingView
from pcb.definition.verification import UNVERIFIED

TOLERANCE_MM = 0.01

Range = tuple[float, float]
Point = tuple[float, float]


@dataclass(frozen=True)
class LandPad:
    """One datasheet pad: number, datasheet pin name and function, supply rail (if any), and its centre, copper size and drill in the datasheet top view (mm)."""

    number: str
    datasheet_name: str
    function: str | None
    rail: str | None = None
    centre_mm: Point | None = None
    size_mm: Point | None = None
    drill_mm: Point | None = None


@dataclass(frozen=True)
class LandPattern:
    """One part's golden facts: product, package, cited source, body size ranges, pads, and the frame rotation and polarity pad where relevant."""

    part_key: str
    mpn: str
    package: str
    source: str
    body_ranges_mm: tuple[Range, Range, Range] | None
    pads: tuple[LandPad, ...]
    frame_rotation_deg: int = 0
    polarity_pad: str | None = None
    internal_groups: tuple[tuple[str, ...], ...] = ()
    # The datasheet draws the land from the side the part sits on (catalogue
    # convention, e.g. JST VH p4 note 1), unless it is fixed by a mating part
    # seen from the board top (the Pi header).
    drawn_from_board_top: bool = False


SOIC16W_PAD = (2.0, 0.6)
SOIC14_PAD = (1.55, 0.6)
PLCC6_PAD = (1.8, 1.2)
SOT23_PAD = (1.3, 0.6)
SULLINS_HOLE = (1.02, 1.02)
TL1105_HOLE = (1.0, 1.0)

# Raspberry Pi 40-pin GPIO header numbering (raspberrypi.com documentation, "GPIO and
# the 40-pin header"): datasheet name, repository semantic pin, rail.
PI_HEADER_PINS = (
    ("3V3", "THREE_VOLTS_THREE", "+3V3"),
    ("5V", "FIVE_VOLTS", "+5V"),
    ("GPIO2 SDA1", "I2C_SDA", None),
    ("5V", "FIVE_VOLTS_ALT", "+5V"),
    ("GPIO3 SCL1", "I2C_SCL", None),
    ("GND", "GROUND_6", "GND"),
    ("GPIO4", "GPIO4", None),
    ("GPIO14 TXD", "UART_TX_GPIO14", None),
    ("GND", "GROUND_9", "GND"),
    ("GPIO15 RXD", "UART_RX_GPIO15", None),
    ("GPIO17", "BUTTON_RESET_GPIO17", None),
    ("GPIO18", "GPIO18", None),
    ("GPIO27", "GPIO27", None),
    ("GND", "GROUND_14", "GND"),
    ("GPIO22", "BUTTON_F3_GPIO22", None),
    ("GPIO23", "BUTTON_F4_GPIO23", None),
    ("3V3", "THREE_VOLTS_THREE_ALT", "+3V3"),
    ("GPIO24", "BUTTON_F5_GPIO24", None),
    ("GPIO10 MOSI", "SPI_DATA_GPIO10", None),
    ("GND", "GROUND_20", "GND"),
    ("GPIO9 MISO", "SPI_MISO_GPIO9", None),
    ("GPIO25", "GPIO25", None),
    ("GPIO11 SCLK", "SPI_CLOCK_GPIO11", None),
    ("GPIO8 CE0", "SPI_CE0_GPIO8", None),
    ("GND", "GROUND_25", "GND"),
    ("GPIO7 CE1", "SPI_CE1_GPIO7", None),
    ("ID_SD", "ID_EEPROM_DATA", None),
    ("ID_SC", "ID_EEPROM_CLOCK", None),
    ("GPIO5", "BUTTON_UP_GPIO5", None),
    ("GND", "GROUND_30", "GND"),
    ("GPIO6", "BUTTON_DOWN_GPIO6", None),
    ("GPIO12", "BUTTON_LEFT_GPIO12", None),
    ("GPIO13", "BUTTON_RIGHT_GPIO13", None),
    ("GND", "GROUND_34", "GND"),
    ("GPIO19", "BUTTON_PASS_GPIO19", None),
    ("GPIO16", "BUTTON_OK_GPIO16", None),
    ("GPIO26", "LED_EN_GPIO26", None),
    ("GPIO20", "BUTTON_F1_GPIO20", None),
    ("GND", "GROUND_39", "GND"),
    ("GPIO21", "BUTTON_F2_GPIO21", None),
)


def _pi_header_pads() -> tuple[LandPad, ...]:
    """Odd pins in the left column, even in the right, pin 1 at the top; 2.54 mm."""
    pads: list[LandPad] = []
    for index, (name, function, rail) in enumerate(PI_HEADER_PINS):
        x = -1.27 if index % 2 == 0 else 1.27
        y = 24.13 - (index // 2) * 2.54
        pads.append(
            LandPad(
                str(index + 1),
                name,
                function,
                rail,
                (x, round(y, 3)),
                None,
                SULLINS_HOLE,
            )
        )
    return tuple(pads)


GOLDEN = (
    LandPattern(
        "SK9822",
        "SK9822-A",
        "PLCC-6 5050",
        # Opsco SPC/SK9822-A Rev 01: p3 §4 mechanical drawing (top view, pin-1
        # chamfer bottom-right; 3 x 1.0 mm leads within 4.2 mm => 1.6 mm pitch;
        # 5.0 x 5.0 body, 5.4 over leads, 1.6 high, +-0.1); p4 §5 pin
        # configuration; p4 §6 recommended PCB land: 1.80 x 1.20 pads, 0.40 apart,
        # 3.40 inner gap => centres +/-2.60 mm.
        "Opsco SPC/SK9822-A Rev 01 p3-p4",
        ((5.3, 5.5), (4.9, 5.1), (1.5, 1.7)),
        (
            LandPad("1", "SDI", "DATA_IN", None, (2.6, -1.6), PLCC6_PAD),
            LandPad("2", "CKI", "CLOCK_IN", None, (2.6, 0.0), PLCC6_PAD),
            LandPad("3", "GND", "GROUND", "GND", (2.6, 1.6), PLCC6_PAD),
            LandPad("4", "VCC", "FIVE_VOLTS", "LED_5V", (-2.6, 1.6), PLCC6_PAD),
            LandPad("5", "CKO", "CLOCK_OUT", None, (-2.6, 0.0), PLCC6_PAD),
            LandPad("6", "SDO", "DATA_OUT", None, (-2.6, -1.6), PLCC6_PAD),
        ),
        polarity_pad="1",
    ),
    LandPattern(
        "TCA9554",
        "TCA9554DWR",
        "SOIC-16W 1.27 mm",
        # TI SCPS233E: p4 §5 pin functions (DW); p39 DW0016A outline (D 10.1-10.5,
        # E1 7.4-7.6, 2.65 max); p40 example board layout ((9.3) row, 16X (2) x
        # 16X (0.6), 14X (1.27)).
        "TI SCPS233E p4, p39-p40 (DW0016A)",
        ((10.1, 10.5), (7.4, 7.6), (0.0, 2.65)),
        (
            LandPad("1", "A0", "ADDRESS_0", None, (-4.65, 4.445), SOIC16W_PAD),
            LandPad("2", "A1", "ADDRESS_1", None, (-4.65, 3.175), SOIC16W_PAD),
            LandPad("3", "A2", "ADDRESS_2", None, (-4.65, 1.905), SOIC16W_PAD),
            LandPad("4", "P0", "P0", None, (-4.65, 0.635), SOIC16W_PAD),
            LandPad("5", "P1", "P1", None, (-4.65, -0.635), SOIC16W_PAD),
            LandPad("6", "P2", "P2", None, (-4.65, -1.905), SOIC16W_PAD),
            LandPad("7", "P3", "P3", None, (-4.65, -3.175), SOIC16W_PAD),
            LandPad("8", "GND", "GROUND", "GND", (-4.65, -4.445), SOIC16W_PAD),
            LandPad("9", "P4", "P4", None, (4.65, -4.445), SOIC16W_PAD),
            LandPad("10", "P5", "P5", None, (4.65, -3.175), SOIC16W_PAD),
            LandPad("11", "P6", "P6", None, (4.65, -1.905), SOIC16W_PAD),
            LandPad("12", "P7", "P7", None, (4.65, -0.635), SOIC16W_PAD),
            LandPad("13", "INT", "INTERRUPT", None, (4.65, 0.635), SOIC16W_PAD),
            LandPad("14", "SCL", "I2C_CLOCK", None, (4.65, 1.905), SOIC16W_PAD),
            LandPad("15", "SDA", "I2C_DATA", None, (4.65, 3.175), SOIC16W_PAD),
            LandPad("16", "VCC", "SUPPLY", "+3V3", (4.65, 4.445), SOIC16W_PAD),
        ),
        polarity_pad="1",
    ),
    LandPattern(
        "LED_SWITCH",
        "Si4403DDY-T1-GE3",
        "SO-8 1.27 mm",
        # Vishay Si4403DDY (S17-0318-Rev A) p1 pinout (1-3 S, 4 G, 5-8 D); package
        # information 71192 (D 4.80-5.00, H 5.80-6.20, A 1.75 max); AN826 (72606
        # p22 = 72286 p33) recommended minimum pads: 0.559 x 1.194 at 1.270, rows 3.861 apart
        # inside => centres +/-2.5275, 4.369 overall along the row.
        "Vishay Si4403DDY p1; 71192; AN826 72606 p22 = 72286 p33",
        ((4.80, 5.00), (5.80, 6.20), (0.0, 1.75)),
        tuple(
            LandPad(number, name, semantic, net, (x, y), (1.194, 0.559))
            for number, name, semantic, net, x, y in (
                ("1", "S1", "SOURCE_1", "+5V", -2.5275, 1.905),
                ("2", "S2", "SOURCE_2", "+5V", -2.5275, 0.635),
                ("3", "S3", "SOURCE_3", "+5V", -2.5275, -0.635),
                ("4", "G", "GATE", None, -2.5275, -1.905),
                ("5", "D5", "DRAIN_5", "LED_5V", 2.5275, -1.905),
                ("6", "D6", "DRAIN_6", "LED_5V", 2.5275, -0.635),
                ("7", "D7", "DRAIN_7", "LED_5V", 2.5275, 0.635),
                ("8", "D8", "DRAIN_8", "LED_5V", 2.5275, 1.905),
            )
        ),
        polarity_pad="1",
        internal_groups=(("S1", "S2", "S3"), ("D5", "D6", "D7", "D8")),
    ),
    LandPattern(
        "LED_SWITCH_DRIVER",
        "BSS138LT1G",
        "SOT-23 (TO-236)",
        # onsemi BSS138LT1/D Rev 15 (Sept 2026) p8 STYLE 21 (1 gate, 2 source,
        # 3 drain); case 318 Issue AU (98ASB42226B) p7: D 2.80-3.04, HE 2.10-2.64,
        # A 0.89-1.11; recommended mounting footprint 3X 0.56 x 3X 0.95, 0.95
        # pitch, 2.90 overall => centres +/-0.975 (reports/datasheets/).
        "onsemi BSS138LT1/D Rev 15 p7-p8; case 318 Issue AU",
        ((2.80, 3.04), (2.10, 2.64), (0.89, 1.11)),
        (
            LandPad("1", "G", "GATE", None, (-0.95, -0.975), (0.56, 0.95)),
            LandPad("2", "S", "SOURCE", "GND", (0.95, -0.975), (0.56, 0.95)),
            LandPad("3", "D", "DRAIN", None, (0.0, 0.975), (0.56, 0.95)),
        ),
        polarity_pad="1",
    ),
)
