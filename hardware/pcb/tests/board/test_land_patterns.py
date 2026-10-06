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
    LandPattern(
        "LED_ENABLE_GATE",
        "SN74LVC1G97DBVR",
        "SOT-23-6 (DBV)",
        # TI SCES416N: p3 pin functions (DBV: 1 In1, 2 GND, 3 In0, 4 Y, 5 VCC, 6 In2);
        # p35 DBV0006A outline (D 2.75-3.05, lead span 2.6-3.0, 1.45 max); p36
        # example board layout: 6X (1.1) x 6X (0.6), 2X (0.95), (2.6) columns.
        "TI SCES416N p3, p35-p36 (DBV0006A)",
        ((2.75, 3.05), (2.6, 3.0), (0.0, 1.45)),
        tuple(
            LandPad(number, name, semantic, net, (x, y), (1.1, 0.6))
            for number, name, semantic, net, x, y in (
                ("1", "In1", "INPUT_1", None, -1.3, 0.95),
                ("2", "GND", "GROUND", "GND", -1.3, 0.0),
                ("3", "In0", "INPUT_0", "+5V", -1.3, -0.95),
                ("4", "Y", "OUTPUT", None, 1.3, -0.95),
                ("5", "VCC", "SUPPLY", "+5V", 1.3, 0.0),
                ("6", "In2", "INPUT_2", None, 1.3, 0.95),
            )
        ),
        polarity_pad="1",
    ),
    LandPattern(
        "AHCT125",
        "SN74AHCT125DR",
        "SOIC-14 1.27 mm",
        # TI SCLS264R: p4 Table 4-1 pin functions (D); p20 D0014A outline (D
        # 8.55-8.75, E 5.8-6.2 lead span, 1.75 max); p21 example board layout
        # ((5.4) row, 14X (1.55) x 14X (0.6), 12X (1.27)).
        "TI SCLS264R p4, p20-p21 (D0014A)",
        ((8.55, 8.75), (5.8, 6.2), (0.0, 1.75)),
        (
            LandPad(
                "1", "1OE", "BUFFER_1_OUTPUT_ENABLE", None, (-2.7, 3.81), SOIC14_PAD
            ),
            LandPad("2", "1A", "BUFFER_1_INPUT", None, (-2.7, 2.54), SOIC14_PAD),
            LandPad("3", "1Y", "BUFFER_1_OUTPUT", None, (-2.7, 1.27), SOIC14_PAD),
            LandPad(
                "4", "2OE", "BUFFER_2_OUTPUT_ENABLE", None, (-2.7, 0.0), SOIC14_PAD
            ),
            LandPad("5", "2A", "BUFFER_2_INPUT", None, (-2.7, -1.27), SOIC14_PAD),
            LandPad("6", "2Y", "BUFFER_2_OUTPUT", None, (-2.7, -2.54), SOIC14_PAD),
            LandPad("7", "GND", "GROUND", "GND", (-2.7, -3.81), SOIC14_PAD),
            LandPad("8", "3Y", "BUFFER_3_OUTPUT", None, (2.7, -3.81), SOIC14_PAD),
            LandPad("9", "3A", "BUFFER_3_INPUT", None, (2.7, -2.54), SOIC14_PAD),
            LandPad(
                "10", "3OE", "BUFFER_3_OUTPUT_ENABLE", None, (2.7, -1.27), SOIC14_PAD
            ),
            LandPad("11", "4Y", "BUFFER_4_OUTPUT", None, (2.7, 0.0), SOIC14_PAD),
            LandPad("12", "4A", "BUFFER_4_INPUT", None, (2.7, 1.27), SOIC14_PAD),
            LandPad(
                "13", "4OE", "BUFFER_4_OUTPUT_ENABLE", None, (2.7, 2.54), SOIC14_PAD
            ),
            LandPad("14", "VCC", "SUPPLY", "+5V", (2.7, 3.81), SOIC14_PAD),
        ),
        polarity_pad="1",
    ),
    LandPattern(
        "HALL_SENSOR",
        "DRV5032FCDBZR",
        "SOT-23-3",
        # TI SLVSDC7H: p3 Figure 5-1 / Table 5-1 (FC, DBZ); p31 DBZ0003A outline
        # (D 2.80-3.04, E1 1.2-1.4, 1.12 max); p32 land pattern example (3X (1.3)
        # x 3X (0.6), (2.1) between rows, 2X (0.95); pin 1 top-left, 3 right).
        # TI land-pattern dimensions run between pad centrelines (the leader lines
        # meet the centre marks), so (2.1) is centre-to-centre: x = +/-1.05.
        "TI SLVSDC7H p3, p31-p32 (DBZ0003A)",
        ((2.80, 3.04), (1.2, 1.4), (0.0, 1.12)),
        (
            LandPad("1", "VCC", "SUPPLY", "+3V3", (-1.05, 0.95), SOT23_PAD),
            LandPad("2", "OUT", "ACTIVE_LOW_OUTPUT", None, (-1.05, -0.95), SOT23_PAD),
            LandPad("3", "GND", "GROUND", "GND", (1.05, 0.0), SOT23_PAD),
        ),
        polarity_pad="1",
    ),
    LandPattern(
        "FUSE_2A",
        "0453002.MR",
        "2410 fuse",
        # Littelfuse 451/453 Series NANO2 (revised January 7, 2009) sheet 60:
        # recommended pad layout 6.86 overall, 3.15 pad height, 1.96 pad width,
        # 2.95 gap; body 6.10 x 2.69 x 2.69 (nominal only; +/-0.05 rounding allowed).
        "Littelfuse 451/453 Series (2009-01-07) p60",
        ((6.05, 6.15), (2.64, 2.74), (2.64, 2.74)),
        (
            LandPad("1", "1", "UNFUSED_INPUT", None, (-2.455, 0.0), (1.96, 3.15)),
            LandPad("2", "2", "FUSED_OUTPUT", None, (2.455, 0.0), (1.96, 3.15)),
        ),
    ),
    LandPattern(
        "TVS_12V0",
        "SMBJ12CA",
        "SMB (DO-214AA)",
        # Littelfuse SMBJ Series (revised 06/03/20) p5 DO-214AA: B 4.06-4.75, C
        # 3.30-3.94, D 1.99-2.61; solder pads I >= 2.26, J = L >= 2.16, K <= 2.74.
        # 2.16 x 2.26 pads (the minimums) with a 2.30 gap (<= K): G 5.21-5.59 and
        # E 0.76-1.52 put the foot within 0.065 mm of the pad's inner edge.
        # Bidirectional (CA): no polarity band; pad 1 faces the eFuse input.
        "Littelfuse SMBJ Series (2020-06-03) p5",
        ((4.06, 4.75), (3.30, 3.94), (1.99, 2.61)),
        (
            LandPad(
                "1", "1", "PROTECTED_INPUT", "DC_FUSED", (-2.23, 0.0), (2.16, 2.26)
            ),
            LandPad("2", "2", "GROUND", "GND", (2.23, 0.0), (2.16, 2.26)),
        ),
    ),
    LandPattern(
        "EFUSE",
        "TPS259474ARPWR",
        "VQFN-HR-10 RPW 2x2 mm",
        # TI SLVSFC9C p73 RPW0010A example board layout (top view; vector drawing
        # read at 85 units/mm and checked against its 2.4 / 1.8 / 1.45 / 0.6 / 0.3 /
        # 0.25 dimensions); p72 body 1.9-2.1 square, 1 mm max. Pads 1, 4, 7, 10 are
        # L-shaped: the 0.6 x 0.3 foot is the anchor here, the leg is checked below.
        # Pin 1 is marked on silk (all pads are rectangles by the drawing).
        "TI SLVSFC9C p72-73 (RPW0010A)",
        ((1.9, 2.1), (1.9, 2.1), (0.9, 1.0)),
        (
            LandPad("1", "EN/UVLO", "ENABLE_UVLO", None, (-0.9, 0.7), (0.6, 0.3)),
            LandPad(
                "2", "OVLO", "OVERVOLTAGE_LOCKOUT", None, (-0.9, 0.225), (0.6, 0.25)
            ),
            LandPad("3", "PG", "POWER_GOOD", None, (-0.9, -0.225), (0.6, 0.25)),
            LandPad(
                "4", "PGTH", "POWER_GOOD_THRESHOLD", None, (-0.9, -0.7), (0.6, 0.3)
            ),
            LandPad("5", "IN", "INPUT", "DC_FUSED", (-0.25, 0.0), (0.3, 2.4)),
            LandPad("6", "OUT", "OUTPUT", "+5V", (0.25, 0.0), (0.3, 2.4)),
            LandPad("7", "DVDT", "SLEW_RATE", None, (0.9, -0.7), (0.6, 0.3)),
            LandPad("8", "GND", "GROUND", "GND", (0.9, -0.225), (0.6, 0.25)),
            LandPad("9", "ILM", "CURRENT_LIMIT", None, (0.9, 0.225), (0.6, 0.25)),
            LandPad("10", "ITIMER", "OVERCURRENT_TIMER", None, (0.9, 0.7), (0.6, 0.3)),
        ),
    ),
    LandPattern(
        "BUTTON",
        "TL1105CF100Q",
        "6x6 mm THT",
        # E-Switch TL1105 series (2.28.2018) p24 order code ("C" = 8.0 mm overall)
        # and p25 TL1105 drawing: 6.00 square body, Ø3.50 stem; P.C. mounting 4 x
        # Ø1.00 holes, 4.50 between 1-3, 6.50 between 1-2; schematic: 1-2 and 3-4
        # are internally connected, the dome bridges the pairs. Nominal +/-0.05.
        "E-Switch TL1105 (2018-02-28) p24-p25",
        ((5.95, 6.05), (5.95, 6.05), (7.95, 8.05)),
        (
            LandPad("1b", "1", "SIGNAL", None, (-2.25, 3.25), None, TL1105_HOLE),
            LandPad("1", "2", "SIGNAL", None, (-2.25, -3.25), None, TL1105_HOLE),
            LandPad("2", "3", "GROUND", "GND", (2.25, 3.25), None, TL1105_HOLE),
            LandPad("2b", "4", "GROUND", "GND", (2.25, -3.25), None, TL1105_HOLE),
        ),
        frame_rotation_deg=-90,
        internal_groups=(("1", "2"), ("3", "4")),
    ),
    LandPattern(
        "CAP_560U",
        "10ZLJ560M8X11.5",
        "radial 8 mm",
        # Rubycon ZLJ catalogue p2: φD 8 => φd 0.6, F 3.5 +/-0.5; body φD+0.5 max,
        # L + α (α = 1.5 for L <= 16). Drill = lead 0.6 + the repository's 0.3 mm THT
        # allowance (ASSUMPTION "CAP_560U drill"). Pad 1 is "+".
        "Rubycon ZLJ catalogue p2, p81",
        ((8.0, 8.5), (8.0, 8.5), (11.5, 13.0)),
        (
            LandPad(
                "1", "+", "SUPPLY_OR_ELECTRODE_A", "+5V", (-1.75, 0.0), None, (0.9, 0.9)
            ),
            LandPad(
                "2", "-", "RETURN_OR_ELECTRODE_B", "GND", (1.75, 0.0), None, (0.9, 0.9)
            ),
        ),
        polarity_pad="1",
    ),
    LandPattern(
        "CAP_100N",
        "CC0603KRX7R9BB104",
        "0603 (1608 metric)",
        # Murata JEMCGC-2701X p25 Table 2 reflow lands for 1.6x0.8 (±0.10): gap a
        # 0.6-0.8, land b 0.6-0.7, width c 0.6-0.8. Mid-range values; a cross-maker
        # land for the same EIA package (no Yageo land on file). Body not checked.
        "Murata JEMCGC-2701X p25 Table 2",
        None,
        (
            LandPad(
                "1", "1", "SUPPLY_OR_ELECTRODE_A", None, (-0.675, 0.0), (0.65, 0.7)
            ),
            LandPad("2", "2", "RETURN_OR_ELECTRODE_B", None, (0.675, 0.0), (0.65, 0.7)),
        ),
    ),
    LandPattern(
        "CAP_10U",
        "CC0805KKX5R6BB106",
        "0805 (2012 metric)",
        # Murata JEMCGC-2701X p25 Table 2 reflow lands for 2.0x1.25 (±0.20): gap a
        # 1.0-1.4, land b 0.6-0.8, width c 1.2-1.4. Mid-range values.
        "Murata JEMCGC-2701X p25 Table 2",
        None,
        (
            LandPad("1", "1", "SUPPLY_OR_ELECTRODE_A", None, (-0.95, 0.0), (0.7, 1.3)),
            LandPad("2", "2", "RETURN_OR_ELECTRODE_B", None, (0.95, 0.0), (0.7, 1.3)),
        ),
    ),
    LandPattern(
        "RES_1K",
        "RC0603FR-071KL",
        "0603 (1608 metric)",
        # Yageo "Chip Resistor Surface Mount — Mounting" (Feb 13, 2018 V.10) p4 Fig. 4
        # / Table 1, size 0603: A 2.6, B 0.8 gap, C 0.9 land length, D 0.8 width.
        "Yageo chip resistor mounting V.10 p4 Table 1",
        None,
        (
            LandPad("1", "1", "TERMINAL_A", None, (-0.85, 0.0), (0.9, 0.8)),
            LandPad("2", "2", "TERMINAL_B", None, (0.85, 0.0), (0.9, 0.8)),
        ),
    ),
    LandPattern(
        "TEST_POINT",
        "S1751-46R",
        "SMD test point",
        # Harwin SMT Hardware p260, S1751-46R (2.00 mm high): body 3.25 x 1.65 x 2.00;
        # recommended PC board pattern 3.45 x 1.85 (nominal; +/-0.05 rounding).
        "Harwin SMT Hardware p260 (S1751-46R)",
        ((3.20, 3.30), (1.60, 1.70), (1.95, 2.05)),
        (LandPad("1", "1", "PROBE", None, (0.0, 0.0), (3.45, 1.85)),),
    ),
    LandPattern(
        "PI_ZERO_HEADER",
        "PPPC202LFBN-RC",
        "2x20 2.54 mm THT",
        # Sullins .100" female header catalogue p81 (recommended P.C. board hole
        # layout Ø.040 [1.02], .100 [2.54] centres, two rows .100 apart) with the
        # Raspberry Pi header numbering above, as the Pi's pins land seen from the
        # board top (the socket is on the bottom; RP-008358-DS-1).
        "Sullins catalogue p81 + Raspberry Pi 40-pin header",
        None,
        _pi_header_pads(),
        polarity_pad="1",
        drawn_from_board_top=True,
    ),
    LandPattern(
        "OLED_HEADER",
        "SM04B-SRSS-TB",
        "SH 4P side entry SMD",
        # JST SH catalogue p1 side-entry land (viewed from the mounting side): four
        # 0.6 x 1.55 pads at 1.0 pitch, pin 1 left, row 4.0..5.55 above the tab row;
        # reinforcement tabs 1.2 x 1.8, inner edge 0.7 beyond the last signal centre,
        # row 0..1.8. Origin midway between rows (2.8375). p3: B 6.0, height 2.9 + 0.05.
        # Pin functions are board-defined (harness soldered by module labels).
        "JST SH catalogue p1, p3",
        ((5.9, 6.1), (4.9, 5.0), (2.9, 3.0)),
        (
            LandPad("1", "1", "GROUND", "GND", (-1.5, 1.9375), (0.6, 1.55)),
            LandPad("2", "2", "THREE_VOLTS_THREE", "+3V3", (-0.5, 1.9375), (0.6, 1.55)),
            LandPad("3", "3", "I2C_CLOCK", None, (0.5, 1.9375), (0.6, 1.55)),
            LandPad("4", "4", "I2C_DATA", None, (1.5, 1.9375), (0.6, 1.55)),
            LandPad("5", "tab", "MOUNTING_TAB_A", "GND", (-2.8, -1.9375), (1.2, 1.8)),
            LandPad("6", "tab", "MOUNTING_TAB_B", "GND", (2.8, -1.9375), (1.2, 1.8)),
        ),
        polarity_pad="1",
    ),
    LandPattern(
        "POWER_HEADER",
        "B4PS-VH",
        "VH 4P side entry THT",
        # JST VH catalogue p3 (side entry B4PS-VH: B 15.78, 10.9 deep, 8.5 high) and
        # p4 layout (viewed from the mounting side): four Ø1.65 (+0.1) holes at 3.96,
        # circuit 1 left, plug from -Y. Origin at the body centre, holes 4.45 above
        # (body from about 1 mm behind the hole row; ASSUMPTION "PTH copper rings").
        "JST VH catalogue p3-p4",
        ((15.7, 15.9), (10.8, 11.0), (8.4, 8.6)),
        (
            LandPad("1", "1", "DC_INPUT", None, (-5.94, 4.45), None, (1.65, 1.65)),
            LandPad("2", "2", "GROUND", "GND", (-1.98, 4.45), None, (1.65, 1.65)),
            LandPad(
                "3", "3", "FUSED_TO_SWITCH", None, (1.98, 4.45), None, (1.65, 1.65)
            ),
            LandPad("4", "4", "RUN", None, (5.94, 4.45), None, (1.65, 1.65)),
        ),
        polarity_pad="1",
    ),
    # S4b eFuse bias and S5 R9 parts on the cited 0603 lands above (same EIA size, same
    # makers' tables; Yageo RT thin film uses the same chip-resistor mounting).
    *(
        LandPattern(
            key,
            mpn,
            "0603 (1608 metric)",
            "Yageo chip resistor mounting V.10 p4 Table 1",
            None,
            (
                LandPad("1", "1", "TERMINAL_A", None, (-0.85, 0.0), (0.9, 0.8)),
                LandPad("2", "2", "TERMINAL_B", None, (0.85, 0.0), (0.9, 0.8)),
            ),
        )
        for key, mpn in (
            ("RES_56", "RC0603FR-0756RL"),
            ("RES_10K", "RC0603FR-0710KL"),
            ("RES_100K", "RC0603FR-07100KL"),
            ("RES_1K65", "RC0603FR-071K65L"),
            ("RES_261K", "RC0603FR-07261KL"),
            ("RES_604K_PRECISION", "RT0603BRD07604KL"),
            ("RES_169K_PRECISION", "RT0603BRD07169KL"),
        )
    ),
    *(
        LandPattern(
            key,
            mpn,
            "0603 (1608 metric)",
            "Murata JEMCGC-2701X p25 Table 2",
            None,
            (
                LandPad(
                    "1", "1", "SUPPLY_OR_ELECTRODE_A", None, (-0.675, 0.0), (0.65, 0.7)
                ),
                LandPad(
                    "2", "2", "RETURN_OR_ELECTRODE_B", None, (0.675, 0.0), (0.65, 0.7)
                ),
            ),
        )
        for key, mpn in (
            ("CAP_10N", "CC0603KRX7R9BB103"),
            ("CAP_1N", "CC0603KRX7R9BB102"),
            ("CAP_1U", "CC0603KRX7R8BB105"),
        )
    ),
)

# Logical pin of a duplicated tactile-switch pad (pcb.definition.native.logical_pin).
DUPLICATE_PADS = {"1b": "1", "2b": "2"}


def _rotate(point: Point, degrees: int) -> Point:
    """Rotate a Y-up datasheet coordinate counter-clockwise by a right angle."""
    radians = math.radians(degrees)
    x, y = point
    return (
        round(x * math.cos(radians) - y * math.sin(radians), 6),
        round(x * math.sin(radians) + y * math.cos(radians), 6),
    )


def _rotate_size(size: Point, degrees: int) -> Point:
    """Pad size as seen after a quarter-turn frame rotation (width and height swap when not a multiple of 180)."""
    return (size[1], size[0]) if degrees % 180 else size


def _datasheet_view(position: pcbnew.VECTOR2I) -> Point:
    """Native template coordinates (Y down) as Y-up millimetres."""
    return (pcbnew.ToMM(position.x), -pcbnew.ToMM(position.y))


class LandPatternTest(unittest.TestCase):
    """Compares the native templates and the placed board with the hand-typed datasheet rows."""

    rails: ClassVar[dict[tuple[str, str], str]]
    references: ClassVar[dict[str, list[str]]]
    led_pads: ClassVar[dict[str, dict[str, pcbnew.VECTOR2I]]]
    led_centres: ClassVar[dict[str, pcbnew.VECTOR2I]]
    placed: ClassVar[dict[str, list[pcbnew.FOOTPRINT]]]
    native_board: ClassVar[pcbnew.BOARD]

    @classmethod
    def setUpClass(cls) -> None:
        """Build the board once and collect rail nets, references and the placed LED pads."""
        native_board = board.load()
        cls.rails = {}
        cls.references = {}
        cls.led_pads = {}
        cls.led_centres = {}
        cls.placed = {}
        cls.native_board = native_board
        for footprint in native.parts(native_board):
            key = footprint.GetFieldText("PartKey")
            if key == "SK9822":
                square = footprint.GetFieldText("Square")
                cls.led_centres[square] = footprint.GetPosition()
                cls.led_pads[square] = {
                    pad.GetNumber(): pad.GetPosition() for pad in footprint.Pads()
                }
            cls.references.setdefault(key, []).append(footprint.GetReference())
            cls.placed.setdefault(key, []).append(footprint)
            for pad in footprint.Pads():
                cls.rails[(footprint.GetReference(), pad.GetNumber())] = (
                    pad.GetNetname()
                )

    def test_every_catalog_part_is_verified_or_explicitly_unverified(self) -> None:
        golden = {pattern.part_key for pattern in GOLDEN}
        self.assertFalse(golden & UNVERIFIED.keys())
        self.assertEqual(golden | UNVERIFIED.keys(), set(PCB_PARTS))
        for key, reason in UNVERIFIED.items():
            with self.subTest(part=key):
                self.assertGreater(len(reason), 20)

    def test_mpn_and_package_match_the_cited_datasheet(self) -> None:
        for golden in GOLDEN:
            with self.subTest(part=golden.part_key):
                part = PCB_PARTS[golden.part_key]
                self.assertEqual(part.spec.mpn, golden.mpn)
                self.assertEqual(part.spec.package, golden.package)
                self.assertEqual(part.template.GetFieldText("Package"), golden.package)
                if golden.body_ranges_mm is None:
                    continue
                body = part.spec.require_body_mm()
                for axis, (value, (low, high)) in enumerate(
                    zip(body, golden.body_ranges_mm, strict=True)
                ):
                    self.assertGreaterEqual(value, low, f"body axis {axis}")
                    self.assertLessEqual(value, high, f"body axis {axis}")

    def test_pad_numbers_carry_the_datasheet_pin_function(self) -> None:
        for golden in GOLDEN:
            part = PCB_PARTS[golden.part_key]
            model = part.new_model("LAND_PATTERN_CHECK")
            template_numbers = {pad.GetNumber() for pad in part.template.Pads()}
            with self.subTest(part=golden.part_key, check="pad set"):
                self.assertEqual(template_numbers, {pad.number for pad in golden.pads})
            for expected in golden.pads:
                if expected.function is None:
                    continue
                with self.subTest(part=golden.part_key, pad=expected.number):
                    logical = DUPLICATE_PADS.get(expected.number, expected.number)
                    pin = model.resolve_endpoint(logical).pin
                    self.assertEqual(
                        pin.name,
                        expected.function,
                        f"{golden.source}: pad {expected.number} is "
                        f"{expected.datasheet_name}",
                    )

    def test_internally_connected_pins_share_a_net_on_the_board(self) -> None:
        for golden in GOLDEN:
            pad_of = {pad.datasheet_name: pad.number for pad in golden.pads}
            for reference in self.references.get(golden.part_key, []):
                for group in golden.internal_groups:
                    with self.subTest(reference=reference, group=group):
                        nets = {self.rails[(reference, pad_of[n])] for n in group}
                        self.assertEqual(len(nets), 1)

    def test_each_binding_declares_the_view_its_datasheet_is_drawn_from(self) -> None:
        for golden in GOLDEN:
            with self.subTest(part=golden.part_key):
                view = PCB_PARTS[golden.part_key].drawing_view
                self.assertEqual(
                    view is DrawingView.BOARD_TOP, golden.drawn_from_board_top
                )

    def test_placed_pads_land_where_the_datasheet_says_in_board_frame(self) -> None:
        for golden in GOLDEN:
            for footprint in self.placed.get(golden.part_key, []):
                turn = footprint.GetOrientationDegrees()
                # A part moved underneath is seen mirrored from the top, unless its
                # land is defined from the board top. KiCad reports 180 - placement.
                mirrored = footprint.IsFlipped() and not golden.drawn_from_board_top
                if footprint.IsFlipped():
                    turn = 180 - turn
                origin = footprint.GetPosition()
                pads = {pad.GetNumber(): pad for pad in footprint.Pads()}
                for expected in golden.pads:
                    if expected.centre_mm is None:
                        continue
                    local = _rotate(expected.centre_mm, golden.frame_rotation_deg)
                    dx, dy = _rotate(local, round(turn))
                    dx = -dx if mirrored else dx
                    pad = pads[expected.number]
                    at = pad.GetPosition()
                    with self.subTest(
                        reference=footprint.GetReference(), pad=expected.number
                    ):
                        self.assertAlmostEqual(
                            pcbnew.ToMM(at.x - origin.x), dx, delta=TOLERANCE_MM
                        )
                        self.assertAlmostEqual(
                            pcbnew.ToMM(origin.y - at.y), dy, delta=TOLERANCE_MM
                        )
                        if expected.size_mm is not None:
                            size = _rotate_size(
                                expected.size_mm,
                                golden.frame_rotation_deg + round(turn),
                            )
                            self.assertAlmostEqual(
                                pcbnew.ToMM(pad.GetSize().x),
                                size[0],
                                delta=TOLERANCE_MM,
                            )
                            self.assertAlmostEqual(
                                pcbnew.ToMM(pad.GetSize().y),
                                size[1],
                                delta=TOLERANCE_MM,
                            )

    def test_pad_geometry_matches_the_datasheet_land_pattern(self) -> None:
        for golden in GOLDEN:
            pads = {
                pad.GetNumber(): pad
                for pad in PCB_PARTS[golden.part_key].template.Pads()
            }
            turn = golden.frame_rotation_deg
            for expected in golden.pads:
                if expected.centre_mm is None:
                    continue
                with self.subTest(part=golden.part_key, pad=expected.number):
                    pad = pads[expected.number]
                    x, y = _datasheet_view(pad.GetPosition())
                    centre = _rotate(expected.centre_mm, turn)
                    self.assertAlmostEqual(x, centre[0], delta=TOLERANCE_MM)
                    self.assertAlmostEqual(y, centre[1], delta=TOLERANCE_MM)
                    if expected.size_mm is not None:
                        size = _rotate_size(expected.size_mm, turn)
                        self.assertAlmostEqual(
                            pcbnew.ToMM(pad.GetSize().x), size[0], delta=TOLERANCE_MM
                        )
                        self.assertAlmostEqual(
                            pcbnew.ToMM(pad.GetSize().y), size[1], delta=TOLERANCE_MM
                        )
                    if expected.drill_mm is None:
                        self.assertEqual(pad.GetAttribute(), pcbnew.PAD_ATTRIB_SMD)
                        continue
                    drill = _rotate_size(expected.drill_mm, turn)
                    self.assertEqual(pad.GetAttribute(), pcbnew.PAD_ATTRIB_PTH)
                    self.assertAlmostEqual(
                        pcbnew.ToMM(pad.GetDrillSize().x), drill[0], delta=TOLERANCE_MM
                    )
                    self.assertAlmostEqual(
                        pcbnew.ToMM(pad.GetDrillSize().y), drill[1], delta=TOLERANCE_MM
                    )

    def test_template_pad_attributes_layers_and_pin_one_shape(self) -> None:
        for key, part in PCB_PARTS.items():
            for pad in part.template.Pads():
                with self.subTest(part=key, pad=pad.GetNumber()):
                    self.assertEqual(pad.GetOrientationDegrees() % 360, 0)
                    self.assertTrue(pad.IsOnLayer(pcbnew.F_Cu))
                    if pad.GetAttribute() == pcbnew.PAD_ATTRIB_SMD:
                        self.assertFalse(pad.IsOnLayer(pcbnew.B_Cu))
                        self.assertTrue(pad.IsOnLayer(pcbnew.F_Mask))
                    else:
                        self.assertEqual(pad.GetAttribute(), pcbnew.PAD_ATTRIB_PTH)
                        self.assertTrue(pad.IsOnLayer(pcbnew.B_Cu))
        for golden in GOLDEN:
            if golden.polarity_pad is None:
                continue
            pads = {
                pad.GetNumber(): pad
                for pad in PCB_PARTS[golden.part_key].template.Pads()
            }
            with self.subTest(part=golden.part_key, check="pin-1 shape"):
                self.assertEqual(
                    pads[golden.polarity_pad].GetShape(), pcbnew.PAD_SHAPE_RECT
                )
                others = [
                    number
                    for number, pad in pads.items()
                    if number != golden.polarity_pad
                    and pad.GetShape() == pcbnew.PAD_SHAPE_RECT
                ]
                self.assertEqual(others, [])

    def test_efuse_corner_pads_carry_the_datasheet_leg(self) -> None:
        # SLVSFC9C p73: corner pads add a 0.25 mm leg at x = -/+0.725 out to
        # y = +/-1.2 (outline x 0.6-1.2, y 0.55-1.2 per corner; area 0.2675 mm2).
        template = PCB_PARTS["EFUSE"].template
        for pad in template.Pads():
            if pad.GetNumber() not in ("1", "4", "7", "10"):
                continue
            outline = pcbnew.SHAPE_POLY_SET()
            pad.TransformShapeToPolygon(
                outline, pcbnew.F_Cu, 0, pcbnew.FromMM(0.001), pcbnew.ERROR_INSIDE
            )
            box = pad.GetBoundingBox()  # includes the custom-pad leg
            extent = (
                abs(
                    pcbnew.ToMM(box.GetLeft() + box.GetRight()) / 2
                    - pcbnew.ToMM(template.GetPosition().x)
                ),
                pcbnew.ToMM(box.GetRight() - box.GetLeft()),
                pcbnew.ToMM(box.GetBottom() - box.GetTop()),
            )
            with self.subTest(pad=pad.GetNumber()):
                self.assertAlmostEqual(extent[0], 0.9, delta=TOLERANCE_MM)
                self.assertAlmostEqual(extent[1], 0.6, delta=TOLERANCE_MM)
                self.assertAlmostEqual(extent[2], 0.65, delta=TOLERANCE_MM)
                self.assertAlmostEqual(outline.Area() / 1e12, 0.2675, delta=0.002)

    def test_supply_pins_reach_their_rails_on_every_placed_part(self) -> None:
        for golden in GOLDEN:
            references = self.references.get(golden.part_key, [])
            with self.subTest(part=golden.part_key, check="placed"):
                self.assertTrue(references)
            for expected in golden.pads:
                if expected.rail is None:
                    continue
                for reference in references:
                    with self.subTest(reference=reference, pad=expected.number):
                        self.assertEqual(
                            self.rails[(reference, expected.number)], expected.rail
                        )

    def test_led_inputs_face_upstream_and_outputs_face_downstream(self) -> None:
        # Datasheet pins: 1 SDI, 2 CKI in; 6 SDO, 5 CKO out. Serpentine A1-H1, H2-A2...
        def distance(a: pcbnew.VECTOR2I, b: pcbnew.VECTOR2I) -> float:
            """Straight-line distance between two native points."""
            return math.hypot(a.x - b.x, a.y - b.y)

        for rank in range(1, 9):
            files = "abcdefgh" if rank % 2 else "hgfedcba"
            chain = [f"{file.upper()}{rank}" for file in files]
            for upstream, downstream in pairwise(chain):
                with self.subTest(link=f"{upstream}->{downstream}"):
                    before = self.led_centres[upstream]
                    after = self.led_centres[downstream]
                    pads_in = self.led_pads[downstream]
                    pads_out = self.led_pads[upstream]
                    for into, out_of in (("1", "6"), ("2", "5")):
                        self.assertLess(
                            distance(pads_in[into], before),
                            distance(pads_in[out_of], before),
                        )
                        self.assertLess(
                            distance(pads_out[out_of], after),
                            distance(pads_out[into], after),
                        )

    def test_rank_turns_keep_outputs_and_inputs_on_the_turning_column_side(
        self,
    ) -> None:
        # H1->H2, H3->H4, ... turn on the +X (H) edge; A2->A3, ... on the -X edge.
        for rank in range(1, 8):
            column = "H" if rank % 2 else "A"
            side = 1 if column == "H" else -1
            upstream, downstream = f"{column}{rank}", f"{column}{rank + 1}"
            with self.subTest(turn=f"{upstream}->{downstream}"):
                for square, pins in ((upstream, ("6", "5")), (downstream, ("1", "2"))):
                    centre = self.led_centres[square].x
                    for pin in pins:
                        offset = self.led_pads[square][pin].x - centre
                        self.assertGreater(side * offset, 0, f"{square} pad {pin}")


if __name__ == "__main__":
    unittest.main()
