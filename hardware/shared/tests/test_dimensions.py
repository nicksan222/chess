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


class DisplayDrawingTest(unittest.TestCase):
    def test_mc242gw_matches_supplier_dimension_drawing(self):
        self.assertEqual(dimensions.PANEL_OLED_SCREEN_OFFSET_MM, (0.005, 2.685))
        self.assertEqual(
            dimensions.PANEL_OLED_MOUNT_HOLES_MM,
            ((-34.0, 19.5), (34.0, 19.5), (-34.0, -19.1), (34.0, -19.1)),
        )
        self.assertEqual(
            dimensions.PANEL_OLED_PAD_POSITIONS_MM,
            (
                (-33.5, -3.81),
                (-33.5, -1.27),
                (-33.5, 1.27),
                (-33.5, 3.81),
                (-33.5, 6.35),
            ),
        )
        self.assertEqual(dimensions.PANEL_OLED_FRAME_MM, (62.1, 38.8, 2.85))
        self.assertEqual(dimensions.PANEL_OLED_PCB_THICKNESS_MM, 1.2)
        self.assertEqual(dimensions.PANEL_OLED_UNDERSIDE_HEIGHT_MM, 2.2)


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
        self.assertEqual(dimensions.PANEL_OLED_SCREEN_SIZE_MM, (55.01, 27.49))
        self.assertLess(
            dimensions.PANEL_OLED_SCREEN_SIZE_MM[0], dimensions.PANEL_OLED_MODULE_MM[0]
        )
        self.assertLess(
            dimensions.PANEL_OLED_SCREEN_SIZE_MM[1], dimensions.PANEL_OLED_MODULE_MM[1]
        )
        self.assertEqual(dimensions.PANEL_OLED_BEZEL_CLEARANCE_XY_MM, 0.5)
        self.assertEqual(dimensions.PANEL_OLED_BEZEL_INNER_MM, (73.0, 44.0))

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

    def test_rear_apertures_hold_the_wired_jack_and_power_switch(self):
        self.assertEqual(dimensions.CASE_JACK_APERTURE_CENTER_X_MM, -141.0)
        self.assertEqual(dimensions.CASE_ROCKER_APERTURE_CENTER_X_MM, -20.0)

    def test_retired_power_references_are_not_reused(self):
        # J3 and SW13 (board-mounted jack and rocker) left the board; reusing the names
        # would make old documents and harness notes silently point at new parts.
        for retired in ("J3", "SW13"):
            self.assertNotIn(retired, dimensions.PCB_STRIP_PLACEMENTS)

    def test_strip_placement_mapping_is_immutable(self):
        # Consumers import the table; an accidental in-place edit would change every domain.
        self.assertIs(type(dimensions.PCB_STRIP_PLACEMENTS), MappingProxyType)


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


class PiTransformTest(unittest.TestCase):
    """J1 is placed from these points, so they are pinned to the RP drawing.

    Negative-ish by design: pin 1 at the microSD end and the odd row nearer the Pi centre
    fail if the transform were mirrored in X or Y, the mistake that would put 5 V on a
    3.3 V pin.
    """

    def test_header_pins_follow_the_agreed_transform(self):
        expected = {
            1: (147.13, -73.73),
            2: (147.13, -76.27),
            39: (98.87, -73.73),
            40: (98.87, -76.27),
        }
        for pin, (x, y) in expected.items():
            with self.subTest(pin=pin):
                actual = dimensions.pi_header_pin_xy(pin)
                self.assertAlmostEqual(actual[0], x)
                self.assertAlmostEqual(actual[1], y)

    def test_pin_numbering_is_the_unmirrored_drawing_view(self):
        """From the PCB top, odd pins form the row nearer the Pi centre."""
        centre_y = dimensions.PI_CENTER_MM[1]
        pitch = dimensions.PI_HEADER_PITCH_MM
        for column in range(20):
            odd = dimensions.pi_header_pin_xy(2 * column + 1)
            even = dimensions.pi_header_pin_xy(2 * column + 2)
            with self.subTest(column=column):
                self.assertAlmostEqual(odd[0], even[0])
                self.assertAlmostEqual(abs(odd[1] - even[1]), pitch)
                self.assertLess(abs(odd[1] - centre_y), abs(even[1] - centre_y))
        # Pin 1 is at the microSD end, which faces the right-wall slot.
        sd_x = dimensions.pi_on_board_xy(dimensions.PI_SD_SOCKET_ON_PI_MM)[0]
        far_x = dimensions.pi_header_pin_xy(39)[0]
        pin1_x = dimensions.pi_header_pin_xy(1)[0]
        self.assertLess(abs(pin1_x - sd_x), abs(far_x - sd_x))

    def test_board_to_board_stack_is_socket_plus_male_header(self):
        # 8.5 mm socket plus 2.54 mm male-header insulator, and the Pi centre derived from
        # the one header anchor.
        self.assertAlmostEqual(dimensions.PI_BOARD_TO_BOARD_MM, 11.04)
        self.assertEqual(dimensions.PI_CENTER_MM, (123.0, -63.5))

    def test_pins_outside_one_to_forty_are_rejected(self):
        for pin in (0, 41):
            with self.subTest(pin=pin), self.assertRaises(ValueError):
                dimensions.pi_header_pin_xy(pin)


class UnverifiedDimensionsTest(unittest.TestCase):
    """The unverified list feeds the PCB release gate, so it must stay truthful."""

    def test_every_flagged_name_is_a_real_shared_dimension(self):
        for name, reason in dimensions.UNVERIFIED_DIMENSIONS.items():
            with self.subTest(name=name):
                self.assertTrue(hasattr(dimensions, name))
                self.assertTrue(reason)

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
