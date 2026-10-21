"""Board positions and the host transform the PCB owns and exports.

Role: tests of `pcb.spec.layout` and `pcb.spec.host`: the table of hand-placed PCB
parts (`PCB_STRIP_PLACEMENTS`), the Pi header transform, the supplier drawings the
case is built around and the list of unverified host dimensions. The expected values
are written out on purpose: moving a part changes PCB routing and the case built from
the export, so it must be done knowingly, not by accident.
"""

import unittest
from dataclasses import replace
from types import MappingProxyType
from unittest.mock import patch

from pcb.spec import host, layout
from pcb.spec.components import oled_module


class BoardFormatTest(unittest.TestCase):
    def test_compact_board_is_smaller_than_a_tournament_board(self):
        self.assertEqual(layout.BOARD_FORMAT, "compact electronic")
        self.assertLess(layout.SQUARE_SIZE_MM, layout.FIDE_REFERENCE_SQUARE_MIN_MM)

    def test_mounting_holes_are_stable(self):
        self.assertEqual(len(layout.PCB_MOUNTING_HOLE_POSITIONS_MM), 20)
        self.assertIn((-120.0, -120.0), layout.PCB_MOUNTING_HOLE_POSITIONS_MM)
        self.assertIn((144.0, -190.0), layout.PCB_MOUNTING_HOLE_POSITIONS_MM)
        self.assertEqual(layout.PCB_MOUNTING_HOLE_DIAMETER_MM, 3.4)


class LayoutValidationTest(unittest.TestCase):
    """Negative cases: the PCB-side checks must reject geometry, not just pass it."""

    def test_a_button_reaching_into_the_playing_area_is_rejected(self):
        button = layout.PANEL_BUTTONS.buttons[0]
        moved = replace(button, position_mm=(button.x_mm, -158.0))
        buttons = replace(
            layout.PANEL_BUTTONS, buttons=(moved, *layout.PANEL_BUTTONS.buttons[1:])
        )
        with (
            patch.object(layout, "PANEL_BUTTONS", buttons),
            self.assertRaisesRegex(ValueError, "off the control strip"),
        ):
            layout.validate()

    def test_a_board_outline_outside_the_compact_range_is_rejected(self):
        deep = (layout.PCB_SIZE_MM[0], 420.0, layout.PCB_SIZE_MM[2])
        with (
            patch.object(layout, "PCB_SIZE_MM", deep),
            self.assertRaisesRegex(ValueError, "compact product range"),
        ):
            layout.validate()

    def test_a_mounting_hole_over_the_pi_is_rejected(self):
        holes = (*layout.PCB_MOUNTING_HOLE_POSITIONS_MM, host.PI_CENTER_MM)
        with (
            patch.object(host, "PCB_MOUNTING_HOLE_POSITIONS_MM", holes),
            self.assertRaisesRegex(ValueError, "over the Pi"),
        ):
            host.validate()


class DisplayDrawingTest(unittest.TestCase):
    def test_mc242gw_matches_supplier_dimension_drawing(self):
        self.assertEqual(oled_module.OLED_SCREEN_SIZE_MM, (55.01, 27.49))
        self.assertEqual(oled_module.OLED_SCREEN_OFFSET_MM, (0.005, 2.685))
        self.assertEqual(
            oled_module.OLED_MOUNT_HOLES_MM,
            ((-34.0, 19.5), (34.0, 19.5), (-34.0, -19.1), (34.0, -19.1)),
        )
        self.assertEqual(
            oled_module.OLED_PAD_POSITIONS_MM,
            (
                (-33.5, -3.81),
                (-33.5, -1.27),
                (-33.5, 1.27),
                (-33.5, 3.81),
                (-33.5, 6.35),
            ),
        )
        self.assertEqual(oled_module.OLED_FRAME_MM, (62.1, 38.8, 2.85))
        self.assertEqual(oled_module.OLED_PCB_THICKNESS_MM, 1.2)
        self.assertEqual(oled_module.OLED_UNDERSIDE_SIZE_MM[2], 2.2)


class StripPlacementTest(unittest.TestCase):
    def test_every_one_off_pcb_position_is_inside_the_board(self):
        half_width = layout.PCB_SIZE_MM[0] / 2.0
        y_max = layout.PLAYING_SPAN_MM / 2.0
        y_min = y_max - layout.PCB_SIZE_MM[1]
        for reference, placement in layout.PCB_STRIP_PLACEMENTS.items():
            with self.subTest(reference=reference):
                x, y = placement.centre_mm
                self.assertGreaterEqual(x, -half_width)
                self.assertLessEqual(x, half_width)
                self.assertGreaterEqual(y, y_min)
                self.assertLessEqual(y, y_max)

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
            for reference, placement in layout.PCB_STRIP_PLACEMENTS.items()
        )

        self.assertEqual(actual, expected)

    def test_retired_power_references_are_not_reused(self):
        # J3 and SW13 (board-mounted jack and rocker) left the board; reusing the names
        # would make old documents and harness notes silently point at new parts.
        for retired in ("J3", "SW13"):
            self.assertNotIn(retired, layout.PCB_STRIP_PLACEMENTS)

    def test_strip_placement_mapping_is_immutable(self):
        # The board build imports the table; an in-place edit would move parts silently.
        self.assertIs(type(layout.PCB_STRIP_PLACEMENTS), MappingProxyType)


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
                actual = host.pi_header_pin_xy(pin)
                self.assertAlmostEqual(actual[0], x)
                self.assertAlmostEqual(actual[1], y)

    def test_pin_numbering_is_the_unmirrored_drawing_view(self):
        """From the PCB top, odd pins form the row nearer the Pi centre."""
        centre_y = host.PI_CENTER_MM[1]
        pitch = host.PI_HEADER_PITCH_MM
        for column in range(20):
            odd = host.pi_header_pin_xy(2 * column + 1)
            even = host.pi_header_pin_xy(2 * column + 2)
            with self.subTest(column=column):
                self.assertAlmostEqual(odd[0], even[0])
                self.assertAlmostEqual(abs(odd[1] - even[1]), pitch)
                self.assertLess(abs(odd[1] - centre_y), abs(even[1] - centre_y))
        # Pin 1 is at the microSD end, which faces the right-wall slot.
        sd_x = host.pi_on_board_xy(host.PI_SD_SOCKET_ON_PI_MM)[0]
        far_x = host.pi_header_pin_xy(39)[0]
        pin1_x = host.pi_header_pin_xy(1)[0]
        self.assertLess(abs(pin1_x - sd_x), abs(far_x - sd_x))

    def test_board_to_board_stack_is_socket_plus_male_header(self):
        # 8.5 mm socket plus 2.54 mm male-header insulator, and the Pi centre derived from
        # the one header anchor.
        self.assertAlmostEqual(host.PI_BOARD_TO_BOARD_MM, 11.04)
        self.assertEqual(host.PI_CENTER_MM, (123.0, -63.5))

    def test_pins_outside_one_to_forty_are_rejected(self):
        for pin in (0, 41):
            with self.subTest(pin=pin), self.assertRaises(ValueError):
                host.pi_header_pin_xy(pin)


class UnverifiedHostDimensionsTest(unittest.TestCase):
    def test_every_flagged_name_is_a_real_host_dimension(self):
        for name, reason in host.UNVERIFIED_HOST_DIMENSIONS.items():
            with self.subTest(name=name):
                self.assertTrue(hasattr(host, name))
                self.assertTrue(reason)


if __name__ == "__main__":
    unittest.main()
