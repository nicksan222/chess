"""Playing-grid and bring-up markings on the board's front silkscreen.

Positions use the shared mechanical origin; the KiCad adapter converts them to
native coordinates. Hole clearances keep grid dots away from screw openings.
"""

from __future__ import annotations

from base import board_placement as placement
from base import rules, sources
from base.design import BoardDesign
from base.kicad import board as kicad
from base.kicad.api import pcbnew
from board import hall_banks
from components.raspberry_pi_header import RaspberryPiHeader
from components.tactile_switch import TactileSwitch
from components.tca9554 import Tca9554

SQUARE_LABEL_OFFSET_MM = (-12.0, 0.0)
SQUARE_GRID_DOT_PITCH_MM = 8.0
SQUARE_GRID_DOT_DIAMETER_MM = 0.6
SQUARE_GRID_DOT_SEGMENT_MM = 0.02
SQUARE_GRID_HOLE_CLEARANCE_MM = 4.0


def square_grid_dot_positions(
    shared: sources.DimensionsSource,
) -> tuple[tuple[float, float], ...]:
    """Return a dotted grid while leaving mounting-hole keepouts clear."""
    half_span = shared.PLAYING_SPAN_MM / 2.0
    boundaries = tuple(
        -half_span + index * shared.SQUARE_SIZE_MM
        for index in range(1, shared.GRID_COUNT)
    )
    steps = round(shared.PLAYING_SPAN_MM / SQUARE_GRID_DOT_PITCH_MM)
    along = tuple(
        -half_span + index * SQUARE_GRID_DOT_PITCH_MM for index in range(1, steps)
    )
    dots = {(boundary, offset) for boundary in boundaries for offset in along}
    dots.update((offset, boundary) for boundary in boundaries for offset in along)
    clearance_squared = SQUARE_GRID_HOLE_CLEARANCE_MM**2
    return tuple(
        sorted(
            (x, y)
            for x, y in dots
            if all(
                (x - hole_x) ** 2 + (y - hole_y) ** 2 >= clearance_squared
                for hole_x, hole_y in shared.PCB_SUPPORT_POSITIONS_MM
            )
        )
    )


def add_square_grid(board: pcbnew.BOARD) -> None:
    """Mark every playing-square boundary with printable silkscreen dots."""
    half_segment = SQUARE_GRID_DOT_SEGMENT_MM / 2.0
    for x, y in square_grid_dot_positions(sources.dimensions()):
        dot = pcbnew.PCB_SHAPE(board)
        dot.SetShape(pcbnew.SHAPE_T_SEGMENT)
        dot.SetStart(kicad.point(x - half_segment, y))
        dot.SetEnd(kicad.point(x + half_segment, y))
        dot.SetLayer(pcbnew.F_SilkS)
        dot.SetWidth(pcbnew.FromMM(SQUARE_GRID_DOT_DIAMETER_MM))
        board.Add(dot)


def _add_text(
    board: pcbnew.BOARD,
    text: str,
    at: tuple[float, float],
    *,
    height: float = rules.SILK_TEXT_HEIGHT_MM,
) -> None:
    label = pcbnew.PCB_TEXT(board)
    label.SetText(text)
    label.SetPosition(kicad.point(*at))
    label.SetLayer(pcbnew.F_SilkS)
    label.SetTextSize(pcbnew.VECTOR2I(pcbnew.FromMM(height), pcbnew.FromMM(height)))
    label.SetTextThickness(pcbnew.FromMM(rules.SILK_LINE_MM))
    board.Add(label)


def add_front_silkscreen(board: pcbnew.BOARD, design: BoardDesign) -> None:
    """Put revision, controls, connector pinout, and bring-up labels on front silkscreen."""
    shared = sources.dimensions()
    _add_text(board, f"CHESS BOARD {design.revision}", (116.0, -165.0), height=1.5)
    _add_text(board, "J3 5V CENTER +", (-144.0, -193.5))
    _add_text(board, "F1 2A MAX", (-137.0, -171.0))
    _add_text(board, "SW13 POWER", (-113.0, -181.5))
    _add_text(board, "J2: GND 3V3 SCL SDA", (-95.0, -165.0), height=0.9)
    _add_text(board, "D1 K=+5V", (-150.0, -159.5), height=0.9)
    _add_text(board, "U5  SPI 3V3 -> LED 5V", (-30.0, -181.0), height=0.8)
    _add_text(board, "R1/R2 I2C PULL-UPS", (-68.0, -166.0), height=0.8)
    _add_text(board, "LED DATA + CLK IN", (-127.0, -118.0), height=0.8)
    _add_text(board, "LED CHAIN END", (146.0, 151.0), height=0.8)

    for name, (x, y) in placement.square_centres(shared).items():
        offset_x, offset_y = SQUARE_LABEL_OFFSET_MM
        _add_text(board, name, (x + offset_x, y + offset_y), height=1.0)

    for bank, component in hall_banks.instances(design):
        item = component.placement
        text = f"{item.reference}  I2C 0x{bank.address:02X}  {bank.label}"
        at = (
            item.x,
            item.y + item.footprint.courtyard[1] / 2 + Tca9554.SILKSCREEN_CLEARANCE_MM,
        )
        _add_text(board, text, at, height=0.8)

    for text, y in zip(
        RaspberryPiHeader.silkscreen_pinout_lines(),
        (-171.0, -176.0, -189.0, -194.0),
        strict=True,
    ):
        _add_text(board, text, (116.0, y), height=0.8)

    button_positions = dict(
        zip(sources.names().BUTTON_NAMES, shared.PANEL_BUTTON_POSITIONS_MM, strict=True)
    )
    for name, (x, y) in button_positions.items():
        offset = TactileSwitch.LABEL_OFFSET_MM
        label_y = y + offset if y > shared.PANEL_ORIGIN_Y_MM else y - offset
        _add_text(board, name, (x, label_y), height=0.9)

    test_points = {
        "5V": (-47.0, -162.5),
        "GND": (-40.0, -162.5),
        "DATA": (-33.0, -162.5),
        "CLK": (-26.0, -162.5),
        "3V3": (-19.0, -162.5),
        "SCL": (-12.0, -162.5),
        "SDA": (-47.0, -193.5),
    }
    for name, at in test_points.items():
        _add_text(board, name, at, height=0.8)
