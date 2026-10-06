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

    def test_bottom_parts_are_the_agreed_through_hole_set(self) -> None:
        self.assertEqual(set(self.bottom), EXPECTED_BOTTOM)
        for footprint in native.parts(self.native_board):
            if footprint.IsFlipped():
                for pad in footprint.Pads():
                    with self.subTest(
                        pad=f"{footprint.GetReference()}-{pad.GetNumber()}"
                    ):
                        self.assertEqual(pad.GetAttribute(), pcbnew.PAD_ATTRIB_PTH)

    def test_bottom_parts_keep_the_chirality_of_their_drawing(self) -> None:
        for footprint in native.parts(self.native_board):
            if footprint.IsFlipped():
                with self.subTest(reference=footprint.GetReference()):
                    self.assertEqual(chirality_errors(footprint), [])

    def test_j4_circuit_one_is_on_the_right_seen_from_below(self) -> None:
        # JST VH p4 (mounting-side view): circuit 1 at the left, opening away from
        # the hole row. Underneath with the opening at +Y, circuit 1 sits at -X.
        header = self.native_board.FindFootprintByReference("J4")
        assert header is not None
        pads = {
            pad.GetNumber(): _relative(header, pad.GetPosition())
            for pad in header.Pads()
        }
        self.assertLess(pads["1"][0], pads["4"][0])
        self.assertGreater(0.0, pads["1"][1], "opening (body) must be at +Y")

    def test_the_old_unmirrored_j4_placement_is_reported(self) -> None:
        scratch = pcbnew.BOARD()
        placement = dimensions.PCB_STRIP_PLACEMENTS["J4"]
        native.place(
            scratch,
            replace(PCB_PARTS["POWER_HEADER"], drawing_view=DrawingView.BOARD_TOP),
            "J4",
            at=placement.centre_mm,
            rotation=placement.rotation_degrees,
            assembly="mutation",
            bottom=True,
        )
        header = scratch.FindFootprintByReference("J4")
        assert header is not None
        self.assertNotEqual(chirality_errors(header), [])

    def test_bottom_parts_clear_the_edge_ledge(self) -> None:
        width, height, _ = dimensions.PCB_SIZE_MM
        top = dimensions.PLAYING_SPAN_MM / 2
        outline = (-width / 2, width / 2, top - height, top)
        keep = dimensions.PCB_BOTTOM_EDGE_KEEPOUT_MM
        for reference, (x0, x1, y0, y1) in self.bottom.items():
            with self.subTest(reference=reference):
                self.assertGreaterEqual(x0 - outline[0], keep)
                self.assertGreaterEqual(outline[1] - x1, keep)
                self.assertGreaterEqual(y0 - outline[2], keep)
                self.assertGreaterEqual(outline[3] - y1, keep)

    def test_bottom_parts_clear_every_support_boss(self) -> None:
        for reference, (x0, x1, y0, y1) in self.bottom.items():
            for bx, by in dimensions.PCB_SUPPORT_POSITIONS_MM:
                gap = math.hypot(max(x0 - bx, 0.0, bx - x1), max(y0 - by, 0.0, by - y1))
                with self.subTest(reference=reference, boss=(bx, by)):
                    self.assertGreaterEqual(gap, BOSS_KEEP_MM)

    def test_bottom_parts_stay_out_of_the_panel_keep_volumes(self) -> None:
        for reference, (x0, x1, y0, y1) in self.bottom.items():
            for name, (
                kx0,
                kx1,
                ky0,
                ky1,
            ) in dimensions.BOTTOM_SIDE_KEEPOUTS_MM.items():
                with self.subTest(reference=reference, keepout=name):
                    overlaps = x0 < kx1 and kx0 < x1 and y0 < ky1 and ky0 < y1
                    self.assertFalse(overlaps)


if __name__ == "__main__":
    unittest.main()
