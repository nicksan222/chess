"""Turn placements and traces into a Gerber layer stack.

This module owns the translation from board coordinates, where the playing area
is centred on the origin, into the positive-quadrant coordinates Gerber files
conventionally use. That happens exactly once, here, so every other module can
think in the same coordinates as the mechanical design.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from gerbonara import ExcellonFile, GerberFile, LayerStack
from gerbonara.apertures import (
    CircleAperture,
    ExcellonTool,
    ObroundAperture,
    RectangleAperture,
)
from gerbonara.graphic_objects import Flash, Line, Region
from gerbonara.utils import MM

import footprints
from core import rules, sources
from core.placement import Placement

BOARD_NAME = "chess-board"


@dataclass
class Trace:
    """A routed segment on one copper layer."""

    net: str
    layer: str
    start: tuple[float, float]
    end: tuple[float, float]
    width: float = rules.TRACE_WIDTH_MM


@dataclass
class Via:
    """A plated hole joining the two copper layers."""

    net: str
    at: tuple[float, float]


@dataclass
class Artwork:
    """Everything that will be written, before it becomes Gerber."""

    traces: list[Trace] = field(default_factory=list)
    vias: list[Via] = field(default_factory=list)
    silk_lines: list[tuple[tuple[float, float], tuple[float, float]]] = field(
        default_factory=list
    )


class Board:
    """The board's extents and the coordinate shift into Gerber space."""

    def __init__(self) -> None:
        shared = sources.dimensions()
        self.width = shared.PCB_SIZE_MM[0]
        self.height = shared.PCB_SIZE_MM[1]
        # Board coordinates: playing area centred, control strip in negative Y.
        self.x_min = -self.width / 2.0
        self.x_max = self.width / 2.0
        self.y_max = shared.PLAYING_SPAN_MM / 2.0
        self.y_min = self.y_max - self.height

    def to_gerber(self, x: float, y: float) -> tuple[float, float]:
        """Shift a board coordinate into the positive quadrant."""
        return (round(x - self.x_min, 4), round(y - self.y_min, 4))

    def contains(self, x: float, y: float, margin: float = 0.0) -> bool:
        return (
            self.x_min + margin <= x <= self.x_max - margin
            and self.y_min + margin <= y <= self.y_max - margin
        )


def _outline(board: Board) -> GerberFile:
    aperture = CircleAperture(rules.OUTLINE_LINE_MM, unit=MM)
    corners = [
        board.to_gerber(board.x_min, board.y_min),
        board.to_gerber(board.x_max, board.y_min),
        board.to_gerber(board.x_max, board.y_max),
        board.to_gerber(board.x_min, board.y_max),
    ]
    objects = []
    for index, start in enumerate(corners):
        end = corners[(index + 1) % len(corners)]
        objects.append(Line(*start, *end, aperture, unit=MM))
    return GerberFile(objects=objects)


def _pad_aperture(pad, expansion: float = 0.0):
    width = pad.width + 2.0 * expansion
    height = pad.height + 2.0 * expansion
    if pad.shape == footprints.base.ROUND:
        return CircleAperture(width, unit=MM)
    if pad.shape == footprints.base.OBLONG:
        return ObroundAperture(width, height, unit=MM)
    return RectangleAperture(width, height, unit=MM)


def _copper_and_mask(
    board: Board, placements: list[Placement], artwork: Artwork
) -> tuple[GerberFile, GerberFile, GerberFile, GerberFile]:
    """Pads and traces on both sides, and the mask openings that clear them."""
    top_copper: list = []
    bottom_copper: list = []
    top_mask: list = []
    bottom_mask: list = []

    for placement in placements:
        for _net_number, _number, (x, y), pad in placement.pads():
            at = board.to_gerber(x, y)
            aperture = _pad_aperture(pad)
            mask = _pad_aperture(pad, rules.MASK_EXPANSION_MM)
            top_copper.append(Flash(*at, aperture, unit=MM))
            top_mask.append(Flash(*at, mask, unit=MM))
            if pad.plated_through:
                # A through-hole pad exists on both sides and is cleared on both.
                bottom_copper.append(Flash(*at, aperture, unit=MM))
                bottom_mask.append(Flash(*at, mask, unit=MM))

    for trace in artwork.traces:
        aperture = CircleAperture(trace.width, unit=MM)
        start = board.to_gerber(*trace.start)
        end = board.to_gerber(*trace.end)
        target = top_copper if trace.layer == "top" else bottom_copper
        target.append(Line(*start, *end, aperture, unit=MM))

    via_pad = CircleAperture(rules.VIA_PAD_MM, unit=MM)
    for via in artwork.vias:
        at = board.to_gerber(*via.at)
        top_copper.append(Flash(*at, via_pad, unit=MM))
        bottom_copper.append(Flash(*at, via_pad, unit=MM))

    return (
        GerberFile(objects=top_copper),
        GerberFile(objects=bottom_copper),
        GerberFile(objects=top_mask),
        GerberFile(objects=bottom_mask),
    )


def _silkscreen(board: Board, artwork: Artwork) -> GerberFile:
    aperture = CircleAperture(rules.SILK_LINE_MM, unit=MM)
    objects = [
        Line(*board.to_gerber(*start), *board.to_gerber(*end), aperture, unit=MM)
        for start, end in artwork.silk_lines
    ]
    return GerberFile(objects=objects)


def _drills(
    board: Board, placements: list[Placement], artwork: Artwork
) -> ExcellonFile:
    """One plated hole per through-hole pad, plus the vias."""
    objects = []
    for placement in placements:
        for _net_number, _number, (x, y), pad in placement.pads():
            if not pad.plated_through:
                continue
            tool = ExcellonTool(pad.drill, plated=True, unit=MM)
            objects.append(Flash(*board.to_gerber(x, y), tool, unit=MM))
    via_tool = ExcellonTool(rules.VIA_DRILL_MM, plated=True, unit=MM)
    for via in artwork.vias:
        objects.append(Flash(*board.to_gerber(*via.at), via_tool, unit=MM))
    return ExcellonFile(objects=objects)


def _ground_pour(
    board: Board,
    placements: list[Placement],
    artwork: Artwork,
    pad_net: dict[tuple[str, str], str],
) -> list:
    """A negative pour: solid copper, then holes knocked out of it.

    Every reed has one leg on ground, so this pour is half of every sense
    connection and most of the power distribution. But a plain filled region
    would short every through-hole pad on the board to ground, which is the
    difference between a ground plane and a scrapped board.

    Gerber solves this the way CAD tools do, with polarity. The pour is painted
    dark, clearances are painted clear to cut holes around every pad that is not
    on ground, and ground pads are then repainted dark so they stay attached.
    Order is significant: later objects paint over earlier ones.
    """
    inset = rules.POUR_TO_OUTLINE_MM
    objects = [
        Region(
            [
                board.to_gerber(board.x_min + inset, board.y_min + inset),
                board.to_gerber(board.x_max - inset, board.y_min + inset),
                board.to_gerber(board.x_max - inset, board.y_max - inset),
                board.to_gerber(board.x_min + inset, board.y_max - inset),
            ],
            unit=MM,
        )
    ]

    reattach = []
    for placement in placements:
        for net_number, _number, (x, y), pad in placement.pads():
            if not pad.plated_through:
                continue
            at = board.to_gerber(x, y)
            on_ground = pad_net.get((placement.reference, net_number)) == "GND"
            if on_ground:
                reattach.append(Flash(*at, _pad_aperture(pad), unit=MM))
            else:
                objects.append(
                    Flash(
                        *at,
                        _pad_aperture(pad, rules.POUR_CLEARANCE_MM),
                        polarity_dark=False,
                        unit=MM,
                    )
                )

    via_clear = CircleAperture(
        rules.VIA_PAD_MM + 2.0 * rules.POUR_CLEARANCE_MM, unit=MM
    )
    via_pad = CircleAperture(rules.VIA_PAD_MM, unit=MM)
    for via in artwork.vias:
        at = board.to_gerber(*via.at)
        if via.net == "GND":
            reattach.append(Flash(*at, via_pad, unit=MM))
        else:
            objects.append(Flash(*at, via_clear, polarity_dark=False, unit=MM))

    return objects + reattach


def build_stack(
    placements: list[Placement],
    artwork: Artwork,
    pad_net: dict[tuple[str, str], str],
) -> LayerStack:
    board = Board()
    top_copper, bottom_copper, top_mask, bottom_mask = _copper_and_mask(
        board, placements, artwork
    )
    # The pour goes down first so the pads and traces above paint over it.
    bottom_copper.objects = (
        _ground_pour(board, placements, artwork, pad_net) + bottom_copper.objects
    )
    return LayerStack(
        graphic_layers={
            ("mechanical", "outline"): _outline(board),
            ("top", "copper"): top_copper,
            ("top", "mask"): top_mask,
            ("top", "silk"): _silkscreen(board, artwork),
            # The LEDs are the only surface-mount parts, so this is the only
            # stencil aperture set. Emitted even though the board is meant to be
            # hand-soldered, because it costs nothing and a fab expects it if
            # anyone ever orders a stencil.
            ("top", "paste"): _paste(board, placements),
            ("bottom", "copper"): bottom_copper,
            ("bottom", "mask"): bottom_mask,
            # Nothing is printed on the underside, but an empty layer is a
            # clearer statement than a missing one.
            ("bottom", "silk"): GerberFile(objects=[]),
            ("bottom", "paste"): GerberFile(objects=[]),
        },
        drill_pth=_drills(board, placements, artwork),
        board_name=BOARD_NAME,
    )


def _paste(board: Board, placements: list[Placement]) -> GerberFile:
    objects = []
    for placement in placements:
        for _net_number, _number, (x, y), pad in placement.pads():
            if pad.plated_through:
                continue
            objects.append(
                Flash(*board.to_gerber(x, y), _pad_aperture(pad), unit=MM)
            )
    return GerberFile(objects=objects)
