"""Negative and positive coverage for automatic current-PCB clearance checks."""

import unittest
from dataclasses import replace

from cad.harness.base.pcb import PcbSnapshot
from shared import dimensions as cad

from .clearance import (
    bottom_side_problem,
    bottom_side_violations,
    local_gap,
    mated_zones,
    square_envelope,
    top_side_violations,
)


class TopSideClearanceTest(unittest.TestCase):
    def test_every_top_side_part_fits_itslocal_gap(self) -> None:
        self.assertEqual(top_side_violations(), {})

    def test_the_gap_check_rejects_a_tall_part_on_top(self) -> None:
        pcb = PcbSnapshot.current()
        tall = replace(
            pcb.parts[0],
            reference="X9",
            body_mm=(8.0, 8.0, 11.5),
            position_mm=(60.0, 0.0),
            bottom=False,
        )
        self.assertIn("X9", top_side_violations(replace(pcb, parts=(*pcb.parts, tall))))

    def test_mated_plugs_follow_actual_position_and_rotation(self) -> None:
        pcb = PcbSnapshot.current()
        connector = next(part for part in pcb.parts if part.reference == "J2")
        moved = replace(connector, position_mm=(10.0, 20.0), rotation_degrees=90.0)
        rect, height = mated_zones(moved)[0]
        self.assertAlmostEqual((rect[0] + rect[1]) / 2, 10.0 + (3.24 + 5.25) / 2)
        self.assertAlmostEqual((rect[2] + rect[3]) / 2, 20.0)
        self.assertEqual(height, 2.95)

    def test_external_display_does_not_reduce_under_plate_clearance(self) -> None:
        rect = square_envelope(
            cad.PANEL_OLED_CENTER_MM, max(cad.PANEL_OLED_MODULE_MM[:2])
        )
        self.assertEqual(local_gap(rect), cad.PCB_TO_PLATE_GAP_MM)


class BottomSideClearanceTest(unittest.TestCase):
    def test_every_bottom_side_part_fits_the_bay(self) -> None:
        self.assertEqual(bottom_side_violations(), {})

    # Negative cases for the bay check: each forbidden spot must be named.
    def test_the_bay_check_rejects_a_part_under_the_pi(self) -> None:
        problem = bottom_side_problem(square_envelope(cad.PI_CENTER_MM, 2.0), 1.25)
        self.assertEqual(problem, "inside the Pi envelope")

    def test_the_bay_check_rejects_a_part_too_tall_for_the_bay(self) -> None:
        self.assertIsNotNone(
            bottom_side_problem(square_envelope((-60.0, 0.0), 10.0), 17.0)
        )

    def test_the_bay_check_rejects_a_part_in_a_panel_keepout(self) -> None:
        x0, x1, y0, y1 = cad.BOTTOM_SIDE_KEEPOUTS_MM["rocker"]
        rect = square_envelope(((x0 + x1) / 2.0, (y0 + y1) / 2.0), 2.0)
        self.assertEqual(
            bottom_side_problem(rect, 1.25), "inside the rocker bay keepout"
        )

    def test_the_bay_check_rejects_a_plug_reaching_the_wall(self) -> None:
        wall_y = cad.CASE_CENTER_OFFSET_Y_MM + cad.CASE_CAVITY_SIZE_MM[1] / 2.0
        rect = (-100.0, -90.0, wall_y - 5.0, wall_y - 0.5)
        self.assertEqual(
            bottom_side_problem(rect, 10.5), "too close to the cavity wall"
        )


if __name__ == "__main__":
    unittest.main()
