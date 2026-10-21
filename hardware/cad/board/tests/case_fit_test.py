"""Case and plate fit numbers around the board the PCB publishes.

Role: tests of `cad/dimensions`: the display and button openings, the case fit
numbers and the list of unverified enclosure dimensions.
"""

import unittest

from cad import dimensions


class PanelFitTest(unittest.TestCase):
    def test_oled_window_matches_the_selected_module_viewing_area(self):
        self.assertEqual(dimensions.PANEL_OLED_SCREEN_SIZE_MM, (55.01, 27.49))
        self.assertLess(
            dimensions.PANEL_OLED_SCREEN_SIZE_MM[0], dimensions.PANEL_OLED_MODULE_MM[0]
        )
        self.assertLess(
            dimensions.PANEL_OLED_SCREEN_SIZE_MM[1], dimensions.PANEL_OLED_MODULE_MM[1]
        )
        self.assertEqual(dimensions.PANEL_OLED_BEZEL_CLEARANCE_XY_MM, 0.5)
        self.assertEqual(dimensions.PANEL_OLED_BEZEL_INNER_MM, (73.0, 44.0))

    def test_rear_apertures_hold_the_wired_jack_and_power_switch(self):
        self.assertEqual(dimensions.CASE_JACK_APERTURE_CENTER_X_MM, -141.0)
        self.assertEqual(dimensions.CASE_ROCKER_APERTURE_CENTER_X_MM, -20.0)


class CaseFitTest(unittest.TestCase):
    """The PCB drops into the case and the plate closes it, by measurement."""

    def test_the_board_outline_and_clearance_fit_the_pocket_at_the_pcb_band(self):
        d = dimensions
        for axis in (0, 1):
            with self.subTest(axis=axis):
                gap = (d.PCB_POCKET_SIZE_MM[axis] - d.PCB_SIZE_MM[axis]) / 2.0
                self.assertGreaterEqual(gap, d.FDM_MIN_FIT_CLEARANCE_MM)
                self.assertLessEqual(gap, d.FDM_MAX_FIT_CLEARANCE_MM)
        # The pocket runs from the ledge top to the plate rim above the board.
        plate_rim_z = d.CASE_HEIGHT_MM - d.TILE_PLATE_REBATE_DEPTH_MM
        self.assertLessEqual(d.PCB_UNDERSIDE_Z_MM + d.PCB_THICKNESS_MM, plate_rim_z)

    def test_the_ledge_carries_every_edge_with_the_board_pushed_anywhere(self):
        d = dimensions
        float_mm = d.PCB_POCKET_CLEARANCE_MM
        for axis in (0, 1):
            for side in (-1.0, 1.0):
                with self.subTest(axis=axis, side=side):
                    edge = side * d.PCB_SIZE_MM[axis] / 2.0
                    cavity = side * d.CASE_CAVITY_SIZE_MM[axis] / 2.0
                    bearing = side * (edge - cavity) - float_mm
                    length = d.CASE_CAVITY_SIZE_MM[1 - axis]
                    self.assertGreater(bearing * length, 0.0)
                    self.assertGreaterEqual(bearing, d.FDM_MIN_FEATURE_MM)
        self.assertGreaterEqual(
            d.PCB_BOTTOM_EDGE_KEEPOUT_MM, d.CASE_PCB_LEDGE_OVERLAP_MM + float_mm
        )

    def test_the_plate_rests_on_a_rim_outboard_of_the_board(self):
        d = dimensions
        for axis in (0, 1):
            with self.subTest(axis=axis):
                self.assertGreater(
                    d.TILE_PLATE_SIZE_MM[axis], d.PCB_POCKET_SIZE_MM[axis]
                )
                self.assertLess(
                    d.CASE_PLATE_REBATE_MM[axis], d.CASE_OUTER_SIZE_MM[axis]
                )

    def test_button_stems_stand_proud_of_the_bezel_within_bounds(self):
        d = dimensions
        protrusion = d.PCB_TOP_Z_MM + d.PANEL_BUTTON_HEIGHT_MM - d.CASE_HEIGHT_MM
        self.assertGreaterEqual(protrusion, d.PANEL_BUTTON_MIN_PROTRUSION_MM)
        self.assertLessEqual(protrusion, d.PANEL_BUTTON_MAX_PROTRUSION_MM)
        self.assertLess(
            d.PANEL_BUTTON_BODY_MM[2],
            d.PCB_TO_PLATE_GAP_MM + d.PANEL_BUTTON_RELIEF_DEPTH_MM,
        )
        self.assertEqual(d.PANEL_BUTTON_HOLE_DIAMETER_MM, 5.0)

    def test_rocker_aperture_is_the_panel_cutout_plus_print_allowance(self):
        d = dimensions
        for aperture, cutout in zip(d.CASE_ROCKER_APERTURE_MM, d.CASE_ROCKER_CUTOUT_MM):
            self.assertAlmostEqual(
                aperture - cutout, 2.0 * d.CASE_ROCKER_PRINT_ALLOWANCE_MM
            )
        rear_wall = (d.CASE_DEPTH_MM - d.CASE_CAVITY_SIZE_MM[1]) / 2.0
        self.assertLess(d.CASE_ROCKER_PANEL_THICKNESS_MM, rear_wall)


class UnverifiedDimensionsTest(unittest.TestCase):
    """Each unverified enclosure value must stay truthful until it is cleared."""

    def test_every_flagged_name_is_a_real_enclosure_dimension(self):
        for name, reason in dimensions.UNVERIFIED_DIMENSIONS.items():
            with self.subTest(name=name):
                self.assertTrue(hasattr(dimensions, name))
                self.assertTrue(reason)

    def test_provisional_host_values_from_the_pcb_stay_flagged(self):
        for name in ("PI_SD_SOCKET_MM", "PI_SD_SOCKET_HEIGHT_MM"):
            with self.subTest(name=name):
                self.assertIn(name, dimensions.UNVERIFIED_DIMENSIONS)

    def test_the_cited_rocker_and_jack_panels_are_no_longer_flagged(self):
        for cleared in (
            "CASE_ROCKER_PANEL_THICKNESS_MM",
            "CASE_ROCKER_CUTOUT_MM",
            "CASE_JACK_NUT_AND_WASHER_MM",
        ):
            with self.subTest(name=cleared):
                self.assertNotIn(cleared, dimensions.UNVERIFIED_DIMENSIONS)
        low, high = dimensions.CASE_ROCKER_PANEL_RANGE_MM
        self.assertLessEqual(low, dimensions.CASE_ROCKER_PANEL_THICKNESS_MM)
        self.assertLessEqual(dimensions.CASE_ROCKER_PANEL_THICKNESS_MM, high)
        self.assertEqual(dimensions.CASE_ROCKER_CUTOUT_MM, (19.4, 13.0))
        self.assertLessEqual(
            dimensions.CASE_JACK_PANEL_THICKNESS_MM, dimensions.CASE_JACK_MAX_PANEL_MM
        )


if __name__ == "__main__":
    unittest.main()
