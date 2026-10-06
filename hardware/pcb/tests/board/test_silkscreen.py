"""Polarity silkscreen and solder-mask webs measured on the native boards.

Polarity pads are typed here from the datasheets cited in `test_land_patterns.py`:
pin 1 of every IC, LED, Hall sensor and connector, the TVS cathode (colour band) and
the electrolytic "+" lead. Clearances use the fabricator minimums in `rules`.
"""

import math
import os
import unittest
from collections import defaultdict
from pathlib import Path
from typing import ClassVar

import pcbnew

from pcb.definition import board, native, rules

PCB_ROOT = Path(__file__).resolve().parents[2]

POLARITY_PADS = {
    "SK9822": "1",
    "TCA9554": "1",
    "AHCT125": "1",
    "HALL_SENSOR": "1",
    "EFUSE": "1",
    "CAP_560U": "1",
    "POWER_HEADER": "1",
    "PI_ZERO_HEADER": "1",
    "OLED_HEADER": "1",
}

# A mark this close to the polarity pad's copper reads as belonging to it.
MARK_REACH_MM = 1.0

GRID_MM = 5.0

Box = tuple[float, float, float, float]
# A rounded rectangle: (left, top, right, bottom, corner radius), in mm.
Shape = tuple[float, float, float, float, float]


def _rounded(pad: pcbnew.PAD, margin: float) -> Shape:
    """Pad copper grown by `margin`: round/oval pads keep their full rounding."""
    box = pad.GetBoundingBox()
    size = pad.GetSize()
    round_pad = pad.GetShape() in (pcbnew.PAD_SHAPE_CIRCLE, pcbnew.PAD_SHAPE_OVAL)
    corner = pcbnew.ToMM(min(size.x, size.y)) / 2 if round_pad else 0.0
    return (
        pcbnew.ToMM(box.GetLeft()) - margin,
        pcbnew.ToMM(box.GetTop()) - margin,
        pcbnew.ToMM(box.GetRight()) + margin,
        pcbnew.ToMM(box.GetBottom()) + margin,
        corner + margin,
    )


def _mask_opening(pad: pcbnew.PAD, board_margin: int) -> Shape:
    """Pad copper grown by its (else the board's) solder-mask expansion."""
    local = pad.GetLocalSolderMaskMargin()
    return _rounded(
        pad, max(pcbnew.ToMM(board_margin if local is None else local), 0.0)
    )


def _copper(pad: pcbnew.PAD) -> Shape:
    """A pad's copper outline as a shape for the mask-web tests."""
    return _rounded(pad, 0.0)


def _circle_to_box(x: float, y: float, radius: float, shape: Shape) -> float:
    """Gap between a circle's edge and a rounded rectangle (negative if overlapping)."""
    left, top, right, bottom, corner = shape
    dx = max(left + corner - x, 0.0, x - (right - corner))
    dy = max(top + corner - y, 0.0, y - (bottom - corner))
    return math.hypot(dx, dy) - corner - radius


def _cells(box: Box | Shape, reach: float) -> list[tuple[int, int]]:
    """Grid cells covered by a box or shape grown by `reach`, for fast neighbour searches."""
    return [
        (ix, iy)
        for ix in range(
            math.floor((box[0] - reach) / GRID_MM),
            math.floor((box[2] + reach) / GRID_MM) + 1,
        )
        for iy in range(
            math.floor((box[1] - reach) / GRID_MM),
            math.floor((box[3] + reach) / GRID_MM) + 1,
        )
    ]


class SilkscreenAndMaskTest(unittest.TestCase):
    """Polarity marks and solder-mask webs on the native and routed boards."""

    native_board: ClassVar[pcbnew.BOARD]

    @classmethod
    def setUpClass(cls) -> None:
        """Build the native board once."""
        cls.native_board = board.load()

    def test_every_polarized_part_has_a_mark_beside_its_polarity_pad(self) -> None:
        # Mask openings per side: a top mark only meets top openings and vice versa.
        apertures: defaultdict[tuple[bool, int, int], list[Shape]] = defaultdict(list)
        margin = self.native_board.GetDesignSettings().m_SolderMaskExpansion
        for footprint in self.native_board.GetFootprints():
            for pad in footprint.Pads():
                opening = _mask_opening(pad, margin)
                for back, layer in ((False, pcbnew.F_Mask), (True, pcbnew.B_Mask)):
                    if pad.IsOnLayer(layer):
                        for cell in _cells(opening, 0.0):
                            apertures[(back, *cell)].append(opening)
        dam = rules.PCBWAY_MIN_MASK_DAM_MM
        placed = 0
        for footprint in native.parts(self.native_board):
            key = footprint.GetFieldText("PartKey")
            if key not in POLARITY_PADS:
                continue
            placed += 1
            reference = footprint.GetReference()
            marks = [
                shape
                for shape in footprint.GraphicalItems()
                if shape.GetLayer()
                == (pcbnew.B_SilkS if footprint.IsFlipped() else pcbnew.F_SilkS)
            ]
            with self.subTest(reference=reference, check="has mark"):
                self.assertTrue(marks)
            pads = {pad.GetNumber(): pad for pad in footprint.Pads()}
            for mark in marks:
                start, end = mark.GetStart(), mark.GetEnd()
                x = pcbnew.ToMM((start.x + end.x) // 2)
                y = pcbnew.ToMM((start.y + end.y) // 2)
                radius = pcbnew.ToMM(mark.GetWidth()) / 2
                with self.subTest(reference=reference, check="mark position"):
                    self.assertGreaterEqual(
                        pcbnew.ToMM(mark.GetWidth()), rules.PCBWAY_MIN_SILK_LINE_MM
                    )
                    gaps = {
                        number: _circle_to_box(x, y, radius, _copper(pad))
                        for number, pad in pads.items()
                    }
                    nearest = min(gaps, key=lambda number: gaps[number])
                    self.assertEqual(nearest, POLARITY_PADS[key])
                    self.assertLessEqual(gaps[nearest], MARK_REACH_MM)
                with self.subTest(reference=reference, check="mark off mask"):
                    worst = min(
                        (
                            _circle_to_box(x, y, radius, opening)
                            for cell in _cells((x, y, x, y), radius + dam)
                            for opening in apertures[(footprint.IsFlipped(), *cell)]
                        ),
                        default=math.inf,
                    )
                    self.assertGreaterEqual(worst, dam - 1e-6)
        self.assertGreater(placed, 0)

    def test_every_via_keeps_a_mask_dam_from_every_pad_opening(self) -> None:
        output = Path(os.environ.get("PCB_OUTPUT", PCB_ROOT / "generated"))
        routed = pcbnew.LoadBoard(str(output / "chess-board.kicad_pcb"))
        margin = routed.GetDesignSettings().m_SolderMaskExpansion
        apertures: defaultdict[tuple[int, int], list[tuple[str, Shape]]] = defaultdict(
            list
        )
        for footprint in routed.GetFootprints():
            for pad in footprint.Pads():
                if not (pad.IsOnLayer(pcbnew.F_Mask) or pad.IsOnLayer(pcbnew.B_Mask)):
                    continue
                opening = _mask_opening(pad, margin)
                label = f"{footprint.GetReference()}-{pad.GetNumber()}"
                for cell in _cells(opening, 0.0):
                    apertures[cell].append((label, opening))
        dam = rules.PCBWAY_MIN_MASK_DAM_MM
        failures: list[str] = []
        vias = [t for t in routed.GetTracks() if isinstance(t, pcbnew.PCB_VIA)]
        self.assertTrue(vias)
        for via in vias:
            at = via.GetPosition()
            x, y = pcbnew.ToMM(at.x), pcbnew.ToMM(at.y)
            radius = pcbnew.ToMM(via.GetWidth(pcbnew.F_Cu)) / 2
            for cell in _cells((x, y, x, y), radius + dam):
                for label, opening in apertures[cell]:
                    gap = _circle_to_box(x, y, radius, opening)
                    if gap < dam - 1e-6:
                        failures.append(
                            f"{via.GetNetname()} via ({x:.2f}, {y:.2f}) {gap:.3f} mm "
                            f"from {label}"
                        )
        self.assertEqual(sorted(set(failures)), [])


if __name__ == "__main__":
    unittest.main()
