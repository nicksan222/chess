"""Cross-domain mechanical positions have one shared authority.

Role: tests of `shared/dimensions` that the PCB and CAD domains rely on: the table of
hand-placed PCB parts (`PCB_STRIP_PLACEMENTS`), the case fit numbers, the Pi header
transform, and the list of unverified dimensions. The expected values are written out on
purpose: moving a part is a cross-domain interface change (PCB routing, CAD clearance and
these tests all read the same table), so it must be done knowingly, not by accident.
"""

import unittest
from types import MappingProxyType

from shared import dimensions


class SharedPlacementTest(unittest.TestCase):
    def test_every_one_off_pcb_position_is_inside_the_board(self):
        half_width = dimensions.PCB_SIZE_MM[0] / 2.0
        y_max = dimensions.PLAYING_SPAN_MM / 2.0
        y_min = y_max - dimensions.PCB_SIZE_MM[1]
        for reference, placement in dimensions.PCB_STRIP_PLACEMENTS.items():
            with self.subTest(reference=reference):
                x, y = placement.centre_mm
                self.assertGreaterEqual(x, -half_width)
                self.assertLessEqual(x, half_width)
                self.assertGreaterEqual(y, y_min)
                self.assertLessEqual(y, y_max)

    def test_oled_window_matches_the_selected_module_viewing_area(self):
        self.assertEqual(dimensions.PANEL_OLED_WINDOW_MM, (23.7, 12.9))
        self.assertLess(
            dimensions.PANEL_OLED_WINDOW_MM[0], dimensions.PANEL_OLED_MODULE_MM[0]
        )
        self.assertLess(
            dimensions.PANEL_OLED_WINDOW_MM[1], dimensions.PANEL_OLED_MODULE_MM[1]
        )
        self.assertEqual(dimensions.PANEL_OLED_RECESS_CLEARANCE_XY_MM, 0.5)
        self.assertEqual(dimensions.PANEL_OLED_RECESS_MM, (28.0, 28.0))

    def test_every_strip_placement_is_stable(self):
        # Golden table of (reference, centre, rotation, bottom side). A change here must be
        # agreed with the PCB engineer, since decoupling, selective-solder and silkscreen
        # tests are tuned to these positions.
        expected = (
            ("J4", (-105.0, 132.45), 180.0, True),
            ("F1", (-108.0, 121.0), 0.0, False),
            ("U74", (-92.0, 132.5), 0.0, False),
            ("D1", (-106.5, 135.4), 180.0, False),
            ("C141", (-94.4, 136.9), 90.0, False),
            ("R4", (-97.4, 133.0), 180.0, False),
            ("C142", (-89.3, 130.1), 0.0, False),
            ("R3", (-88.9, 132.5), 270.0, False),
            ("C143", (-88.4, 135.0), 0.0, False),
            ("C144", (-85.9, 130.6), 180.0, False),
            ("R5", (-83.0, 130.6), 0.0, False),
            ("R6", (-83.0, 133.2), 0.0, False),
            ("R7", (-75.5, 133.2), 0.0, False),
            ("R8", (-83.0, 135.8), 0.0, False),
            ("C2", (-87.6, 139.0), 0.0, False),
            ("C1", (-66.0, 132.0), 0.0, True),
            ("C140", (-56.0, 132.0), 0.0, True),
            ("J2", (-110.0, -158.5), 0.0, False),
            ("U5", (-70.0, -180.0), 0.0, False),
            ("C7", (-66.5, -174.2), 0.0, False),
            ("R9", (-79.0, -178.73), 0.0, False),
            ("Q1", (-55.0, -188.0), 0.0, False),
            ("C145", (-55.0, -192.8), 0.0, False),
            ("R16", (-60.0, -192.8), 0.0, False),
            ("Q2", (-55.0, -179.5), 0.0, False),
            ("R13", (-50.0, -183.0), 180.0, False),
            ("R14", (-50.0, -179.0), 0.0, False),
            ("R15", (-59.5, -176.0), 0.0, False),
            ("U75", (-70.0, -190.0), 180.0, False),
            ("C146", (-70.0, -193.0), 0.0, False),
            ("TP1", (-47.0, -165.0), 0.0, False),
            ("TP2", (-40.0, -165.0), 0.0, False),
            ("TP3", (-87.5, -178.73), 0.0, False),
            ("TP4", (-83.0, -182.5), 0.0, False),
            ("R17", (-87.5, -182.5), 0.0, False),
            ("R18", (-83.0, -185.5), 0.0, False),
            ("TP5", (-19.0, -165.0), 0.0, False),
            ("TP6", (-12.0, -165.0), 0.0, False),
            ("TP7", (-47.0, -196.0), 0.0, False),
        )
        actual = tuple(
            (
                reference,
                placement.centre_mm,
                placement.rotation_degrees,
                placement.bottom,
            )
            for reference, placement in dimensions.PCB_STRIP_PLACEMENTS.items()
        )

        self.assertEqual(actual, expected)

    def test_rear_apertures_align_with_jack_and_power_switch(self):
        self.assertEqual(dimensions.PCB_STRIP_PLACEMENTS["J3"].x_mm, -150.0)
        self.assertEqual(dimensions.PCB_STRIP_PLACEMENTS["SW13"].x_mm, -113.0)

    def test_strip_placement_mapping_is_immutable(self):
        self.assertIs(type(dimensions.PCB_STRIP_PLACEMENTS), MappingProxyType)


if __name__ == "__main__":
    unittest.main()
