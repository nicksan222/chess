"""Mechanical fit against shared CAD dimensions and approved native land patterns."""

import unittest
from itertools import combinations

import pcbnew

from pcb.definition import board, native, rules
from pcb.definition.parts import catalog as parts
from shared import dimensions


def bounds(footprint):
    points = [
        p
        for shape in footprint.GraphicalItems()
        if shape.GetLayer() == pcbnew.F_CrtYd
        for p in (shape.GetStart(), shape.GetEnd())
    ]
    return (
        min(p.x for p in points),
        min(p.y for p in points),
        max(p.x for p in points),
        max(p.y for p in points),
    )


class DimensionsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.board = board.load()
        cls.parts = native.parts(cls.board)
        cls.by_ref = {f.GetReference(): f for f in cls.board.GetFootprints()}

    def test_outline_mounting_holes_and_coordinate_orientation(self):
        edges = [
            s for s in self.board.GetDrawings() if s.GetLayer() == pcbnew.Edge_Cuts
        ]
        xs = [s.GetStart().x for s in edges]
        ys = [s.GetStart().y for s in edges]
        self.assertEqual(
            (pcbnew.ToMM(max(xs) - min(xs)), pcbnew.ToMM(max(ys) - min(ys))),
            dimensions.PCB_SIZE_MM[:2],
        )
        self.assertEqual(
            (min(xs), min(ys)), (native.point(-160, 160).x, native.point(-160, 160).y)
        )
        self.assertLess(native.point(0, 1).y, native.point(0, 0).y)
        holes = [
            f
            for f in self.by_ref.values()
            if f.GetReference().startswith("H")
            and not f.GetReference().startswith("HS")
        ]
        self.assertEqual(
            {(f.GetPosition().x, f.GetPosition().y) for f in holes},
            {
                (native.point(x, y).x, native.point(x, y).y)
                for x, y in dimensions.PCB_SUPPORT_POSITIONS_MM
            },
        )
        for footprint in holes:
            pad = next(iter(footprint.Pads()))
            self.assertEqual(pad.GetAttribute(), pcbnew.PAD_ATTRIB_NPTH)
            self.assertEqual(
                pcbnew.ToMM(pad.GetDrillSize().x),
                dimensions.PCB_MOUNTING_HOLE_DIAMETER_MM,
            )

    def test_square_grid_offsets_and_bank_alignment(self):
        centres = board.square_centres()
        self.assertEqual(
            (centres["A1"], centres["H8"]), ((-140.0, -140.0), (140.0, 140.0))
        )
        self.assertEqual(centres["B1"][0] - centres["A1"][0], dimensions.SQUARE_SIZE_MM)
        for name, (x, y) in centres.items():
            with self.subTest(square=name):
                members = [
                    f
                    for f in self.parts
                    if f.GetFieldText("Assembly") == f"square/{name}"
                ]
                sensor = next(
                    f for f in members if f.GetFieldText("PartKey") == "HALL_SENSOR"
                )
                led = next(f for f in members if f.GetFieldText("PartKey") == "SK9822")
                lx, ly = (
                    x + dimensions.LED_POSITION_MM[0],
                    y + dimensions.LED_POSITION_MM[1],
                )
                self.assertEqual(sensor.GetPosition(), native.point(x, y))
                self.assertEqual(led.GetPosition(), native.point(lx, ly))
                self.assertEqual(
                    led.GetOrientationDegrees() % 360,
                    180 if int(name[1]) % 2 == 0 else 0,
                )
                expected = {
                    (native.point(lx, ly - 8).x, native.point(lx, ly - 8).y),
                    (native.point(x, y - 3).x, native.point(x, y - 3).y),
                }
                self.assertEqual(
                    {
                        (f.GetPosition().x, f.GetPosition().y)
                        for f in members
                        if f.GetFieldText("PartKey") == "CAP_100N"
                    },
                    expected,
                )
        for f in self.parts:
            if f.GetFieldText("PartKey") == "TCA9554":
                at = dimensions.EXPANDER_POSITIONS_BY_BANK_MM[f.GetFieldText("Bank")]
                self.assertEqual(f.GetPosition(), native.point(*at))
                bank = next(
                    b
                    for b in dimensions.HALL_BANKS
                    if b.label == f.GetFieldText("Bank")
                )
                cx, cy = bank.centre(
                    dimensions.SQUARE_SIZE_MM, dimensions.PLAYING_SPAN_MM
                )
                self.assertEqual(at, (cx, cy + 2))

    def test_panel_buttons_connectors_and_rotated_jack_slots(self):
        actual = {
            (f.GetPosition().x, f.GetPosition().y)
            for f in self.parts
            if f.GetFieldText("PartKey") == "BUTTON"
        }
        self.assertEqual(
            actual,
            {
                (native.point(x, y).x, native.point(x, y).y)
                for x, y in dimensions.PANEL_BUTTON_POSITIONS_MM
            },
        )
        for ref, (x, y, angle) in dimensions.PCB_STRIP_PLACEMENTS_MM.items():
            with self.subTest(reference=ref):
                f = self.by_ref[ref]
                self.assertEqual(f.GetPosition(), native.point(x, y))
                self.assertEqual(f.GetOrientationDegrees() % 360, angle % 360)
        self.assertEqual(
            self.by_ref["J1"].GetPosition(), native.point(*dimensions.PI_BAY_CENTER_MM)
        )
        self.assertEqual(
            self.by_ref["J1"].GetOrientationDegrees() % 360,
            dimensions.PI_HEADER_ROTATION_DEG % 360,
        )
        jack = self.by_ref["J3"]
        self.assertEqual(
            {
                (pcbnew.ToMM(p.GetDrillSize().x), pcbnew.ToMM(p.GetDrillSize().y))
                for p in jack.Pads()
            },
            {(1.6, 1.0)},
        )
        self.assertEqual(
            {
                p.GetNumber(): (
                    pcbnew.ToMM(p.GetPosition().x - jack.GetPosition().x),
                    pcbnew.ToMM(jack.GetPosition().y - p.GetPosition().y),
                )
                for p in jack.Pads()
            },
            {"1": (-3.0, 0.0), "2": (3.0, 0.0), "3": (0.0, 4.7)},
        )

    def test_courtyards_pads_and_leads_fit_without_overlap(self):
        left, top = native.point(-160, 160).x, native.point(-160, 160).y
        right, bottom = native.point(160, -200).x, native.point(160, -200).y
        boxes = {f.GetReference(): bounds(f) for f in self.parts}
        for a, b in combinations(boxes, 2):
            x0, y0, x1, y1 = boxes[a]
            u0, v0, u1, v1 = boxes[b]
            self.assertFalse(
                x0 < u1 and u0 < x1 and y0 < v1 and v0 < y1,
                f"courtyard overlap: {a}, {b}",
            )
        for f in self.parts:
            with self.subTest(reference=f.GetReference()):
                x0, y0, x1, y1 = boxes[f.GetReference()]
                self.assertTrue(left <= x0 < x1 <= right and top <= y0 < y1 <= bottom)
                for pad in f.Pads():
                    p, size = pad.GetPosition(), pad.GetSize()
                    self.assertTrue(x0 <= p.x - size.x / 2 <= p.x + size.x / 2 <= x1)
                    self.assertTrue(y0 <= p.y - size.y / 2 <= p.y + size.y / 2 <= y1)
                    self.assertGreater(min(size.x, size.y), 0)
                    if pad.GetAttribute() == pcbnew.PAD_ATTRIB_PTH:
                        drill = pad.GetDrillSize()
                        for copper, hole in ((size.x, drill.x), (size.y, drill.y)):
                            self.assertGreaterEqual(
                                pcbnew.ToMM(hole), rules.PCBWAY_MIN_DRILL_MM
                            )
                            self.assertGreaterEqual(
                                pcbnew.ToMM(copper - hole) / 2,
                                rules.PCBWAY_MIN_ANNULAR_RING_MM,
                            )
        for template in parts.TEMPLATES.values():
            for a, b in combinations(template.Pads(), 2):
                dx = (
                    abs(a.GetPosition().x - b.GetPosition().x)
                    - (a.GetSize().x + b.GetSize().x) / 2
                )
                dy = (
                    abs(a.GetPosition().y - b.GetPosition().y)
                    - (a.GetSize().y + b.GetSize().y) / 2
                )
                self.assertGreater(max(dx, dy), 0, "overlapping physical pads")
