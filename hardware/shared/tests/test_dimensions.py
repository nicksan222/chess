"""Cross-domain mechanical positions have one shared authority."""

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
        expected = (
            ("J3", (-150.0, -178.0), -90.0),
            ("F1", (-138.0, -178.0), 0.0),
            ("D1", (-150.0, -165.0), 0.0),
            ("SW13", (-113.0, -190.0), 0.0),
            ("C1", (-128.0, -170.0), 0.0),
            ("C2", (-116.0, -168.0), 0.0),
            ("J2", (-95.0, -172.0), 0.0),
            ("U5", (-70.0, -180.0), 0.0),
            ("C7", (-58.0, -180.0), 0.0),
            ("R1", (-50.0, -170.0), 0.0),
            ("R2", (-50.0, -176.0), 0.0),
            ("TP1", (-47.0, -165.0), 0.0),
            ("TP2", (-40.0, -165.0), 0.0),
            ("TP3", (-33.0, -165.0), 0.0),
            ("TP4", (-26.0, -165.0), 0.0),
            ("TP5", (-19.0, -165.0), 0.0),
            ("TP6", (-12.0, -165.0), 0.0),
            ("TP7", (-47.0, -196.0), 0.0),
        )
        actual = tuple(
            (reference, placement.centre_mm, placement.rotation_degrees)
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
