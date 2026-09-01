"""Compose components and mechanical board geometry in KiCad."""

from __future__ import annotations

from pathlib import Path
from types import ModuleType

from base import board_placement as placement
from base import rules, sources
from base.kicad import board as kicad
from base.kicad.api import pcbnew
from board import definition as board_definition
from board.wiring.nets import Net

BOARD_EDGE_WIDTH_MM = 0.05
SQUARE_LABEL_OFFSET_MM = (-12.0, 0.0)
SQUARE_GRID_DOT_PITCH_MM = 8.0
SQUARE_GRID_DOT_DIAMETER_MM = 0.6
SQUARE_GRID_DOT_SEGMENT_MM = 0.02
SQUARE_GRID_HOLE_CLEARANCE_MM = 4.0

EXPANDER_LABELS = (
    ("U1  I2C 0x20  A1-D4", (-66.0, -94.0)),
    ("U2  I2C 0x21  E1-H4", (94.0, -94.0)),
    ("U3  I2C 0x22  A5-D8", (-66.0, 66.0)),
    ("U4  I2C 0x23  E5-H8", (94.0, 66.0)),
)

PI_HEADER_PINOUT = (
    "J1 PI: 3 SDA  5 SCL  7 IRQ  11 RESET  15 F3",
    "16 F4  18 F5  19 SPI-DATA  23 SPI-CLK",
    "29 UP  31 DOWN  32 LEFT  33 RIGHT  35 PASS  36 OK",
    "38 F1  40 F2 | 1/17 3V3 | 2/4 5V | GND: 6/9/14/20/25/30/34/39",
)


class BoardGeometry:
    """Mechanical and plane geometry attached to one native KiCad layout."""

    def __init__(self, layout: kicad.KiCadBoard) -> None:
        self.layout = layout

    def add_mechanical_features(self) -> None:
        _add_outline(self.layout.native)
        _add_mounting_holes(self.layout.native)
        _add_square_grid(self.layout.native)
        _add_front_silkscreen(
            self.layout.native,
            self.layout.design.revision
            if self.layout.design
            else sources.netlist()["revision"],
        )

    def add_power_planes(self) -> None:
        _add_power_planes(self.layout.native, self.layout.nets)


class NativeBoardWriter:
    """Final native KiCad serialization and router export stage."""

    def __init__(self, layout: kicad.KiCadBoard) -> None:
        self.layout = layout

    def write(self, board_path: Path, dsn_path: Path) -> None:
        _write_board(self.layout.native, board_path, dsn_path)


def _add_mounting_holes(board: pcbnew.BOARD) -> None:
    """Add one plated-copper-free screw clearance over every case boss."""
    shared = sources.dimensions()
    diameter = shared.PCB_MOUNTING_HOLE_DIAMETER_MM
    for index, (x, y) in enumerate(shared.PCB_SUPPORT_POSITIONS_MM, 1):
        module = pcbnew.FOOTPRINT(board)
        module.SetReference(f"H{index}")
        module.SetValue("M3 mounting hole")
        module.SetBoardOnly(True)
        module.SetExcludedFromBOM(True)
        module.SetExcludedFromPosFiles(True)
        module.Reference().SetVisible(False)
        module.Value().SetVisible(False)
        module.SetPosition(kicad.point(x, y))
        board.Add(module)
        pad = pcbnew.PAD(module)
        pad.SetNumber("")
        pad.SetPosition(kicad.point(x, y))
        pad.SetAttribute(pcbnew.PAD_ATTRIB_NPTH)
        size = pcbnew.FromMM(diameter)
        pad.SetSize(pcbnew.VECTOR2I(size, size))
        pad.SetDrillSize(pcbnew.VECTOR2I(size, size))
        pad.SetShape(pcbnew.PAD_SHAPE_CIRCLE)
        pad.SetLayerSet(pad.UnplatedHoleMask())
        module.Add(pad)
        radius = diameter / 2 + 0.5
        corners = (
            (x - radius, y - radius),
            (x + radius, y - radius),
            (x + radius, y + radius),
            (x - radius, y + radius),
        )
        for corner_index, start in enumerate(corners):
            line = pcbnew.PCB_SHAPE(module)
            line.SetShape(pcbnew.SHAPE_T_SEGMENT)
            line.SetStart(kicad.point(*start))
            line.SetEnd(kicad.point(*corners[(corner_index + 1) % 4]))
            line.SetLayer(pcbnew.F_CrtYd)
            line.SetWidth(pcbnew.FromMM(0.05))
            module.Add(line)


def _square_grid_dot_positions(
    shared: ModuleType,
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


def _add_square_grid(board: pcbnew.BOARD) -> None:
    """Mark every playing-square boundary with printable silkscreen dots."""
    half_segment = SQUARE_GRID_DOT_SEGMENT_MM / 2.0
    for x, y in _square_grid_dot_positions(sources.dimensions()):
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
    height: float = 1.0,
) -> None:
    label = pcbnew.PCB_TEXT(board)
    label.SetText(text)
    label.SetPosition(kicad.point(*at))
    label.SetLayer(pcbnew.F_SilkS)
    label.SetTextSize(pcbnew.VECTOR2I(pcbnew.FromMM(height), pcbnew.FromMM(height)))
    label.SetTextThickness(pcbnew.FromMM(rules.SILK_LINE_MM))
    board.Add(label)


def _add_front_silkscreen(board: pcbnew.BOARD, revision: str) -> None:
    """Put revision, controls, connector pinout, and bring-up labels on copper."""
    shared = sources.dimensions()
    _add_text(board, f"CHESS BOARD {revision}", (116.0, -165.0), height=1.5)
    _add_text(board, "J3 5V CENTER +", (-144.0, -193.5))
    _add_text(board, "F1 2A MAX", (-137.0, -171.0))
    _add_text(board, "SW13 POWER", (-113.0, -181.5))
    _add_text(board, "J2: GND 3V3 SCL SDA", (-95.0, -165.0), height=0.9)
    _add_text(board, "D1 K=+5V", (-150.0, -159.5), height=0.9)
    _add_text(board, "U5  SPI 3V3 -> LED 5V", (-30.0, -181.0), height=0.8)
    _add_text(board, "R1/R2 I2C PULL-UPS", (-68.0, -166.0), height=0.8)
    _add_text(board, "R3 IRQ PULL-UP", (-19.0, -177.0), height=0.8)
    _add_text(board, "LED DATA + CLK IN", (-127.0, -118.0), height=0.8)
    _add_text(board, "LED CHAIN END", (146.0, 151.0), height=0.8)

    for name, (x, y) in placement.square_centres(shared).items():
        offset_x, offset_y = SQUARE_LABEL_OFFSET_MM
        _add_text(board, name, (x + offset_x, y + offset_y), height=1.0)

    for text, at in EXPANDER_LABELS:
        _add_text(board, text, at, height=0.8)

    for text, y in zip(PI_HEADER_PINOUT, (-171.0, -176.0, -189.0, -194.0), strict=True):
        _add_text(board, text, (116.0, y), height=0.8)

    button_positions = dict(
        zip(sources.names().BUTTON_NAMES, shared.PANEL_BUTTON_POSITIONS_MM, strict=True)
    )
    for name, (x, y) in button_positions.items():
        label_y = y + 6.5 if y > shared.PANEL_ORIGIN_Y_MM else y - 6.5
        _add_text(board, name, (x, label_y), height=0.9)

    test_points = {
        "5V": (-47.0, -162.5),
        "GND": (-40.0, -162.5),
        "DATA": (-33.0, -162.5),
        "CLK": (-26.0, -162.5),
        "3V3": (-19.0, -162.5),
        "SCL": (-12.0, -162.5),
        "SDA": (-47.0, -193.5),
        "IRQ": (-40.0, -193.5),
    }
    for name, at in test_points.items():
        _add_text(board, name, at, height=0.8)


def _add_outline(board: pcbnew.BOARD) -> None:
    dimensions = sources.dimensions()
    width, height, _thickness = dimensions.PCB_SIZE_MM
    x0, x1 = -width / 2, width / 2
    y1 = dimensions.PLAYING_SPAN_MM / 2
    y0 = y1 - height
    corners = ((x0, y0), (x1, y0), (x1, y1), (x0, y1))
    for index, start in enumerate(corners):
        edge = pcbnew.PCB_SHAPE(board)
        edge.SetShape(pcbnew.SHAPE_T_SEGMENT)
        edge.SetStart(kicad.point(*start))
        edge.SetEnd(kicad.point(*corners[(index + 1) % 4]))
        edge.SetLayer(pcbnew.Edge_Cuts)
        edge.SetWidth(pcbnew.FromMM(BOARD_EDGE_WIDTH_MM))
        board.Add(edge)


def _add_power_planes(board, net_by_name) -> None:
    """Add inset ground, 5 V, and 3.3 V zones on dedicated internal layers."""
    envelope = board_definition.envelope()
    corners = (
        (envelope.x_min + 1, envelope.y_min + 1),
        (envelope.x_max - 1, envelope.y_min + 1),
        (envelope.x_max - 1, envelope.y_max - 1),
        (envelope.x_min + 1, envelope.y_max - 1),
    )
    for name, layer in (
        (Net.GROUND, pcbnew.In1_Cu),
        (Net.FIVE_VOLTS, pcbnew.In2_Cu),
        (Net.THREE_VOLTS_THREE, pcbnew.In3_Cu),
    ):
        zone = pcbnew.ZONE(board)
        zone.SetNet(net_by_name[name])
        zone.SetLayer(layer)
        zone.Outline().NewOutline()
        for x, y in corners:
            at = kicad.point(x, y)
            zone.Outline().Append(at.x, at.y)
        board.Add(zone)


def _write_board(
    board: pcbnew.BOARD,
    board_path: Path,
    dsn_path: Path,
) -> None:
    """Fill zones, save the native board, and export its router interchange file."""
    pcbnew.SaveBoard(str(board_path), board)
    filled = pcbnew.LoadBoard(str(board_path))
    pcbnew.ZONE_FILLER(filled).Fill(filled.Zones())
    temporary = board_path.with_suffix(".filled.kicad_pcb")
    pcbnew.SaveBoard(str(temporary), filled)
    temporary.replace(board_path)
    temporary.with_suffix(".kicad_pro").unlink(missing_ok=True)

    filled = pcbnew.LoadBoard(str(board_path))
    dsn_path.parent.mkdir(parents=True, exist_ok=True)
    if not pcbnew.ExportSpecctraDSN(filled, str(dsn_path)):
        raise RuntimeError("KiCad failed to export the autorouter design")
