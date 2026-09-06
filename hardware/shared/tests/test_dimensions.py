"""Cross-domain mechanical positions have one shared authority."""

import unittest

from shared import dimensions


class SharedPlacementTest(unittest.TestCase):
    def test_every_one_off_pcb_position_is_inside_the_board(self):
        half_width = dimensions.PCB_SIZE_MM[0] / 2.0
        y_max = dimensions.PLAYING_SPAN_MM / 2.0
        y_min = y_max - dimensions.PCB_SIZE_MM[1]
        for reference, (x, y, _rotation) in dimensions.PCB_STRIP_PLACEMENTS_MM.items():
            with self.subTest(reference=reference):
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

    def test_connector_and_switch_access_references_are_shared(self):
        self.assertIn("J3", dimensions.PCB_STRIP_PLACEMENTS_MM)
        self.assertIn("SW13", dimensions.PCB_STRIP_PLACEMENTS_MM)


if __name__ == "__main__":
    unittest.main()
