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
    )
)
