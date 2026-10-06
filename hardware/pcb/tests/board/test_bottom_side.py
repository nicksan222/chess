"""Bottom-side parts stay out of the case ledge, the bosses and the panel volumes.

The case (shared/dimensions/case.py, interface S3a M1-M5) supports the board on a
perimeter ledge (PCB_BOTTOM_EDGE_KEEPOUT_MM from the outline), on Ø7 bosses at
PCB_SUPPORT_POSITIONS_MM (keep 1.0 mm beyond the boss radius), and reserves
BOTTOM_SIDE_KEEPOUTS_MM below the board for the rear-wall jack and rocker.
"""

import math
import unittest
from dataclasses import replace
from typing import ClassVar

import pcbnew

from pcb.definition import board, native
from pcb.definition.parts.catalog import PCB_PARTS
from pcb.definition.parts.part import DrawingView
from shared import dimensions

BOSS_KEEP_MM = dimensions.PCB_SUPPORT_BOSS_DIAMETER_MM / 2 + 1.0
EXPECTED_BOTTOM = frozenset({"J1", "J4", "C1", "C140"})

Box = tuple[float, float, float, float]
Point = tuple[float, float]


def _relative(footprint: pcbnew.FOOTPRINT, at: pcbnew.VECTOR2I) -> Point:
    """Offset from the footprint origin in mm, Y up, seen from the board top."""
    origin = footprint.GetPosition()
    return (pcbnew.ToMM(at.x - origin.x), pcbnew.ToMM(origin.y - at.y))


def chirality_errors(footprint: pcbnew.FOOTPRINT) -> list[str]:
    """Pads not where a rigid turn of the drawing puts them, from the drawn side.

    A mounting-side drawing must match the part as seen from below (the side it
    sits on); a board-top drawing must match as seen from above. Only rotations
    are allowed, so a mirrored part (pads plus origin offset) cannot match.
    """
    part = PCB_PARTS[footprint.GetFieldText("PartKey")]
    from_below = part.drawing_view is DrawingView.MOUNTING_SIDE
    drawn = {
        p.GetNumber(): _relative(part.template, p.GetPosition())
        for p in part.template.Pads()
    }
    seen: dict[str, Point] = {}
    for pad in footprint.Pads():
        x, y = _relative(footprint, pad.GetPosition())
        seen[pad.GetNumber()] = (-x if from_below else x, y)
    for quarter in range(4):
        c, s = (
            round(math.cos(quarter * math.pi / 2)),
            round(math.sin(quarter * math.pi / 2)),
        )
        if all(
            math.hypot(c * x - s * y - seen[n][0], s * x + c * y - seen[n][1]) < 0.01
            for n, (x, y) in drawn.items()
        ):
            return []
    return [f"{footprint.GetReference()}: pads are a mirror image of the drawing"]


def _shared_box(footprint: pcbnew.FOOTPRINT) -> Box:
    """Courtyard and pads of a footprint in shared mm (x0, x1, y0, y1, Y up)."""
    points = [
        point
        for shape in footprint.GraphicalItems()
        if shape.GetLayer() in (pcbnew.F_CrtYd, pcbnew.B_CrtYd)
        for point in (shape.GetStart(), shape.GetEnd())
    ]
    for pad in footprint.Pads():
        box = pad.GetBoundingBox()
        points += [
            pcbnew.VECTOR2I(box.GetLeft(), box.GetTop()),
            pcbnew.VECTOR2I(box.GetRight(), box.GetBottom()),
        ]
    xs = [pcbnew.ToMM(p.x) - native.ORIGIN_X_MM for p in points]
    ys = [native.ORIGIN_Y_MM - pcbnew.ToMM(p.y) for p in points]
    return (min(xs), max(xs), min(ys), max(ys))


class BottomSideTest(unittest.TestCase):
    """Bottom-side parts keep clear of the ledge, bosses and panel volumes."""

    bottom: ClassVar[dict[str, Box]]
    native_board: ClassVar[pcbnew.BOARD]

    @classmethod
    def setUpClass(cls) -> None:
        """Build the board and collect the bottom-side footprints' shared-frame boxes once."""
        cls.native_board = board.load()
        cls.bottom = {
            f.GetReference(): _shared_box(f)
            for f in native.parts(cls.native_board)
            if f.IsFlipped()
        }
