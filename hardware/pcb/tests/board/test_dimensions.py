"""Mechanical fit against shared CAD dimensions and approved native land patterns.

Role: checks the built board against `shared.dimensions`: the outline and mounting holes,
every square, LED and Hall position, the bank/expander alignment, panel parts, and that
courtyards, pads and leads do not overlap. These are the geometric promises the case and
plate rely on. Evidence type: software test of the native board, not of a printed fit.
"""

import unittest
from itertools import combinations

import pcbnew

from pcb.definition import board, native, rules
from pcb.definition.bank_assemblies import BANK_ASSEMBLIES
from pcb.definition.parts import catalog as parts
from shared import dimensions


def bounds(footprint: pcbnew.FOOTPRINT) -> tuple[int, int, int, int]:
    """A footprint's courtyard bounds (left, top, right, bottom) in native units."""
    points = [
        p
        for shape in footprint.GraphicalItems()
        if shape.GetLayer() in (pcbnew.F_CrtYd, pcbnew.B_CrtYd)
        for p in (shape.GetStart(), shape.GetEnd())
    ]
    return (
        min(p.x for p in points),
        min(p.y for p in points),
        max(p.x for p in points),
        max(p.y for p in points),
    )


class DimensionsTest(unittest.TestCase):
    """Board envelope, squares, banks, panel parts, courtyards and pads against the shared dimensions."""

    @classmethod
    def setUpClass(cls):
        """Build the board once and index its footprints."""
        cls.board = board.load()
        cls.parts = native.parts(cls.board)
        cls.by_ref = {f.GetReference(): f for f in cls.board.GetFootprints()}

    def test_outline_mounting_holes_and_coordinate_orientation(self):
        edges = [
            shape
            for item in self.board.GetDrawings()
            if isinstance(item, pcbnew.PCB_SHAPE)
            and item.GetLayer() == pcbnew.Edge_Cuts
            for shape in (item,)
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
        centres = {square.name: square.centre_mm for square in dimensions.BOARD_SQUARES}
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
                # SK9822 datasheet top view has inputs (pins 1-2) on +X.
                self.assertEqual(
                    led.GetOrientationDegrees() % 360,
                    0 if int(name[1]) % 2 == 0 else 180,
                )
                # Bypass caps on the supply-pin side (tests/board/test_decoupling.py):
                # the LED cap turns with the LED, the Hall cap sits 2.4 mm below.
                side = 4 if int(name[1]) % 2 == 0 else -4
                expected = {
                    (native.point(lx, ly + side).x, native.point(lx, ly + side).y),
                    (native.point(x, y - 2.4).x, native.point(x, y - 2.4).y),
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
                bank_assembly = next(
                    assembly
                    for assembly in BANK_ASSEMBLIES
                    if assembly.label == f.GetFieldText("Bank")
                )
                at = bank_assembly.expander_position_mm
                self.assertEqual(f.GetPosition(), native.point(*at))
                cx, cy = bank_assembly.bank.centre(
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
                for x, y in (button.position_mm for button in dimensions.PANEL_BUTTONS)
            },
        )
        for ref, placement in dimensions.PCB_STRIP_PLACEMENTS.items():
            with self.subTest(reference=ref):
                f = self.by_ref[ref]
                self.assertEqual(f.GetPosition(), native.point(*placement.centre_mm))
                # A back-side part is flipped: KiCad reports 180 - rotation.
                rotation = placement.rotation_degrees
                expected = (180 - rotation if placement.bottom else rotation) % 360
                self.assertEqual(f.GetOrientationDegrees() % 360, expected)
                self.assertEqual(f.IsFlipped(), placement.bottom)
        # J1 hangs the Pi from the bottom side at the shared Pi transform; its 40
        # pads are checked against pi_header_pin_xy in test_pi_header.py.
        header = self.by_ref["J1"]
        self.assertEqual(
            header.GetPosition(), native.point(*dimensions.PI_HEADER_CENTER_MM)
        )
        self.assertTrue(header.IsFlipped())
        # JST VH catalogue p4: J4 holes Ø1.65 at 3.96 mm, row at (-105, +128), the
        # body (origin) 4.45 mm past the row toward the +Y opening. The drawing is
        # the mounting-side view, so from the top circuit 1 is at -X (S3c B1).
        entry = self.by_ref["J4"]
        self.assertEqual(
            {
                p.GetNumber(): (
                    round(pcbnew.ToMM(p.GetPosition().x) - native.ORIGIN_X_MM, 2),
                    round(native.ORIGIN_Y_MM - pcbnew.ToMM(p.GetPosition().y), 2),
                    pcbnew.ToMM(p.GetDrillSize().x),
                )
                for p in entry.Pads()
            },
            {
                "1": (-110.94, 128.0, 1.65),
                "2": (-106.98, 128.0, 1.65),
                "3": (-103.02, 128.0, 1.65),
                "4": (-99.06, 128.0, 1.65),
            },
        )
        self.assertGreater(
            native.ORIGIN_Y_MM - pcbnew.ToMM(entry.GetPosition().y), 128.0
        )

    def test_courtyards_pads_and_leads_fit_without_overlap(self):
        left, top = native.point(-160, 160).x, native.point(-160, 160).y
        right, bottom = native.point(160, -200).x, native.point(160, -200).y
        boxes = {f.GetReference(): bounds(f) for f in self.parts}
        side = {f.GetReference(): f.IsFlipped() for f in self.parts}
        for a, b in combinations(boxes, 2):
            if side[a] != side[b]:
                continue  # opposite sides; plated holes are checked by DRC
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
        for part in parts.PCB_PARTS.values():
            for a, b in combinations(part.template.Pads(), 2):
                dx = (
                    abs(a.GetPosition().x - b.GetPosition().x)
                    - (a.GetSize().x + b.GetSize().x) / 2
                )
                dy = (
                    abs(a.GetPosition().y - b.GetPosition().y)
                    - (a.GetSize().y + b.GetSize().y) / 2
                )
                self.assertGreater(max(dx, dy), 0, "overlapping physical pads")
