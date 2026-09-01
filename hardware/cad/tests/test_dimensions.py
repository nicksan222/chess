"""Tests for physical scale and relationships shared by the Blender projects.

`core/dimensions.py` validates its own internal consistency when imported. These
tests cover what that cannot: product-level facts a reader would want stated, and
the relationships between the two printed parts and the board between them.
"""

from math import isclose
from pathlib import Path
import sys
import unittest


CAD_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CAD_ROOT))

from core import dimensions as cad  # noqa: E402


class UnitContractTest(unittest.TestCase):
    def test_blender_units_are_millimetres(self) -> None:
        self.assertTrue(
            isclose(cad.BLENDER_SCALE_LENGTH * cad.MILLIMETRES_PER_METRE, 1.0)
        )

    def test_case_has_a_plausible_inch_conversion(self) -> None:
        for span in (cad.CASE_WIDTH_MM, cad.CASE_DEPTH_MM):
            inches = span / cad.MILLIMETRES_PER_INCH
            self.assertGreater(inches, 12.0)
            self.assertLess(inches, 16.0)


class ProductScaleTest(unittest.TestCase):
    def test_board_is_explicitly_compact(self) -> None:
        self.assertEqual(cad.BOARD_FORMAT, "compact electronic")
        self.assertLess(cad.SQUARE_SIZE_MM, cad.FIDE_REFERENCE_SQUARE_MIN_MM)

    def test_forty_millimetre_squares_suit_an_ordinary_chess_set(self) -> None:
        """A square wants to be about 1.25x the king's base diameter."""
        self.assertEqual(cad.SQUARE_SIZE_MM, 40.0)
        largest_king_base = cad.SQUARE_SIZE_MM / 1.25
        self.assertGreaterEqual(largest_king_base, 32.0)

    def test_chessboard_is_eight_square_pitches_across(self) -> None:
        self.assertEqual(cad.GRID_COUNT, 8)
        self.assertTrue(
            isclose(cad.PLAYING_SPAN_MM, cad.SQUARE_SIZE_MM * cad.GRID_COUNT)
        )
        self.assertEqual(cad.PLAYING_SPAN_MM, 320.0)

    def test_the_case_is_deeper_than_it_is_wide_by_the_control_strip(self) -> None:
        self.assertTrue(
            isclose(
                cad.CASE_DEPTH_MM - cad.CASE_WIDTH_MM, cad.PANEL_STRIP_DEPTH_MM
            )
        )


class TwoPrintedPartsTest(unittest.TestCase):
    """Revision A needed 129 prints for a board. This needs two."""

    def test_there_are_exactly_two_printed_parts(self) -> None:
        self.assertEqual(len(cad.PRINTED_PART_SIZES_MM), 2)

    def test_no_per_tile_enclosure_dimensions_survive(self) -> None:
        for gone in (
            "TILE_BOTTOM_HEIGHT_MM",
            "TILE_TOP_THICKNESS_MM",
            "TILE_LID_CLEARANCE_MM",
            "TILE_WIRE_PORT_WIDTH_MM",
            "TILE_VELCRO_PAD_SIZE_MM",
            "TILE_MOUNT_SCREW_POSITIONS_MM",
            "BOARD_TRAY_OUTER_SIZE_MM",
            "MAGNET_RING_OUTER_DIAMETER_MM",
        ):
            self.assertFalse(hasattr(cad, gone), gone)

    def test_the_plate_covers_the_playing_area_with_a_fit_clearance(self) -> None:
        self.assertTrue(
            isclose(
                cad.TILE_PLATE_SPAN_MM,
                cad.PLAYING_SPAN_MM - cad.TILE_PLATE_CLEARANCE_MM,
            )
        )
        self.assertLess(cad.TILE_PLATE_SPAN_MM, cad.PLAYING_SPAN_MM)


class PrintEnvelopeTest(unittest.TestCase):
    def test_both_parts_fit_a_print_service(self) -> None:
        for part in cad.PRINTED_PART_SIZES_MM:
            self.assertTrue(
                cad.fits_build_volume(part, cad.REFERENCE_SERVICE_BUILD_VOLUME_MM),
                part,
            )

    def test_neither_part_fits_a_desktop_printer(self) -> None:
        """Stated rather than assumed: these parts have to be quoted out."""
        for part in cad.PRINTED_PART_SIZES_MM:
            self.assertFalse(
                cad.fits_build_volume(part, cad.REFERENCE_DESKTOP_BUILD_VOLUME_MM),
                part,
            )

    def test_metre_scale_error_cannot_fit_reference_printer(self) -> None:
        """A unit slip is the failure this guardrail exists to catch."""
        wrong_scale = tuple(
            axis * cad.MILLIMETRES_PER_METRE for axis in cad.TILE_PLATE_SIZE_MM
        )
        self.assertFalse(
            cad.fits_build_volume(wrong_scale, cad.REFERENCE_SERVICE_BUILD_VOLUME_MM)
        )


class VerticalStackTest(unittest.TestCase):
    """The case, the board and the plate have to add up to one height."""

    def test_the_stack_sums_to_the_case_height(self) -> None:
        total = (
            cad.CASE_FLOOR_MM
            + cad.PI_BAY_HEIGHT_MM
            + cad.PCB_THICKNESS_MM
            + cad.PCB_TO_PLATE_GAP_MM
            + cad.TILE_PLATE_THICKNESS_MM
        )
        self.assertTrue(isclose(total, cad.CASE_HEIGHT_MM))

    def test_the_plate_sits_flush_with_the_case_top(self) -> None:
        plate_top = (
            cad.CASE_HEIGHT_MM - cad.TILE_PLATE_REBATE_DEPTH_MM
        ) + cad.TILE_PLATE_THICKNESS_MM
        self.assertTrue(isclose(plate_top, cad.CASE_HEIGHT_MM))

    def test_the_cavity_clears_the_pi_on_its_header(self) -> None:
        needed = (
            cad.PI_HEADER_HEIGHT_MM + cad.PI_BOARD_SIZE_MM[2] + cad.PI_CLEARANCE_MM
        )
        self.assertGreaterEqual(cad.PI_BAY_HEIGHT_MM, needed)

    def test_the_plate_clears_the_tallest_thing_on_the_board(self) -> None:
        tallest = max(
            cad.HALL_SENSOR_HEIGHT_MM + cad.HALL_SENSOR_STANDOFF_MM,
            cad.LED_PACKAGE_MAX_SIZE_MM[2],
            cad.EXPANDER_BODY_MM[2],
        )
        self.assertGreater(cad.PCB_TO_PLATE_GAP_MM, tallest)


class FdmFeatureTest(unittest.TestCase):
    def test_fit_clearance_stays_in_prototype_range(self) -> None:
        self.assertGreaterEqual(
            cad.TILE_PLATE_CLEARANCE_MM, cad.FDM_MIN_FIT_CLEARANCE_MM
        )
        self.assertLessEqual(
            cad.TILE_PLATE_CLEARANCE_MM, cad.FDM_MAX_FIT_CLEARANCE_MM
        )

    def test_structural_features_exceed_minimums(self) -> None:
        for name, value in (
            ("case wall", cad.CASE_WALL_MM),
            ("case floor", cad.CASE_FLOOR_MM),
            ("case frame", cad.CASE_FRAME_WIDTH_MM),
            ("plate thickness", cad.TILE_PLATE_THICKNESS_MM),
            ("diffuser skin", cad.TILE_PLATE_DIFFUSER_SKIN_MM),
            ("plate rib", cad.TILE_PLATE_RIB_WIDTH_MM),
        ):
            with self.subTest(feature=name):
                self.assertTrue(cad.meets(value, cad.FDM_MIN_FEATURE_MM))

    def test_engraved_lines_are_at_least_two_nozzle_widths(self) -> None:
        """A narrower slot does not resolve when printed."""
        self.assertTrue(
            cad.meets(
                cad.TILE_PLATE_GROOVE_WIDTH_MM, 2.0 * cad.FDM_REFERENCE_NOZZLE_MM
            )
        )

    def test_a_dark_square_over_an_led_keeps_a_printable_skin(self) -> None:
        remaining = (
            cad.TILE_PLATE_DIFFUSER_SKIN_MM - cad.TILE_PLATE_DARK_SQUARE_DEPTH_MM
        )
        self.assertTrue(cad.meets(remaining, cad.FDM_MIN_FEATURE_MM))

    def test_meets_tolerates_decimal_subtraction(self) -> None:
        """1.2 - 0.4 is not exactly 0.8 in binary floating point."""
        self.assertTrue(cad.meets(1.2 - 0.4, 0.8))
        self.assertFalse(cad.meets(0.79, 0.8))


class PerSquareFeatureTest(unittest.TestCase):
    def test_one_led_and_one_hall_sensor_for_every_square(self) -> None:
        squares = cad.GRID_COUNT * cad.GRID_COUNT
        self.assertEqual(len(cad.BOARD_SQUARE_CENTERS_MM), squares)
        self.assertEqual(len(cad.BOARD_LED_POSITIONS_MM), squares)
        self.assertEqual(len(cad.BOARD_HALL_POSITIONS_MM), squares)

    def test_positions_are_unique(self) -> None:
        for name, table in (
            ("led", cad.BOARD_LED_POSITIONS_MM),
            ("hall", cad.BOARD_HALL_POSITIONS_MM),
        ):
            with self.subTest(table=name):
                self.assertEqual(
                    len({(x, y) for _r, _c, x, y in table}), len(table)
                )

    def test_every_feature_lands_inside_the_playing_area(self) -> None:
        limit = cad.PLAYING_SPAN_MM / 2.0
        for _row, _column, x, y in cad.BOARD_LED_POSITIONS_MM:
            self.assertLess(abs(x) + cad.TILE_PLATE_LED_POCKET_MM[0] / 2.0, limit)
            self.assertLess(abs(y) + cad.TILE_PLATE_LED_POCKET_MM[1] / 2.0, limit)

    def test_an_led_pocket_stays_within_its_own_square(self) -> None:
        """A pocket crossing a grid line would light two squares at once."""
        half = cad.SQUARE_SIZE_MM / 2.0
        for axis, offset in enumerate(cad.LED_POSITION_MM):
            edge = abs(offset) + cad.TILE_PLATE_LED_POCKET_MM[axis] / 2.0
            self.assertLess(edge, half)

    def test_the_checkerboard_is_half_dark(self) -> None:
        self.assertEqual(
            len(cad.BOARD_DARK_SQUARES_MM), cad.GRID_COUNT * cad.GRID_COUNT // 2
        )
        for row, column, _x, _y in cad.BOARD_DARK_SQUARES_MM:
            self.assertEqual((row + column) % 2, 1)

    def test_hall_sensor_dimensions_have_explicit_xy_and_height(self) -> None:
        self.assertEqual(cad.HALL_SENSOR_BODY_MM, (2.92, 1.30))
        self.assertEqual(cad.HALL_SENSOR_HEIGHT_MM, 1.12)

    def test_underside_pockets_clear_the_hall_sensors(self) -> None:
        self.assertGreater(
            cad.TILE_PLATE_UNDERSIDE_POCKET_SPAN_MM, cad.HALL_SENSOR_BODY_MM[0]
        )
        self.assertTrue(
            isclose(
                cad.TILE_PLATE_UNDERSIDE_POCKET_SPAN_MM,
                cad.SQUARE_SIZE_MM - 2.0 * cad.TILE_PLATE_RIB_WIDTH_MM,
            )
        )


class ExpanderEnvelopeTest(unittest.TestCase):
    def test_all_four_quadrant_positions_are_shared_with_pcb_placement(self) -> None:
        self.assertEqual(
            set(cad.EXPANDER_POSITIONS_BY_QUADRANT_MM),
            {"A1-D4", "E1-H4", "A5-D8", "E5-H8"},
        )
        self.assertEqual(cad.EXPANDER_BODY_MM, (10.3, 17.9, 2.65))


class BoardSupportTest(unittest.TestCase):
    def test_the_board_spans_the_playing_area_and_the_strip(self) -> None:
        self.assertTrue(isclose(cad.PCB_SIZE_MM[0], cad.PLAYING_SPAN_MM))
        self.assertTrue(
            isclose(
                cad.PCB_SIZE_MM[1], cad.PLAYING_SPAN_MM + cad.PANEL_STRIP_DEPTH_MM
            )
        )

    def test_a_320_mm_panel_gets_interior_support(self) -> None:
        """Perimeter support alone lets a board this size flex."""
        self.assertGreaterEqual(len(cad.PCB_SUPPORT_POSITIONS_MM), 16)
        self.assertEqual(
            len(set(cad.PCB_SUPPORT_POSITIONS_MM)),
            len(cad.PCB_SUPPORT_POSITIONS_MM),
        )

    def test_every_support_stands_clear_of_an_led_and_a_hall_sensor(self) -> None:
        radius = cad.PCB_SUPPORT_BOSS_DIAMETER_MM / 2.0
        for boss_x, boss_y in cad.PCB_SUPPORT_POSITIONS_MM:
            for _row, _column, led_x, led_y in cad.BOARD_LED_POSITIONS_MM:
                clear = max(abs(boss_x - led_x), abs(boss_y - led_y))
                self.assertGreaterEqual(
                    clear, radius + cad.TILE_PLATE_LED_POCKET_MM[0] / 2.0
                )

    def test_supports_reach_the_underside_of_the_board(self) -> None:
        self.assertTrue(
            isclose(
                cad.CASE_FLOOR_MM + cad.PI_BAY_HEIGHT_MM, cad.PCB_UNDERSIDE_Z_MM
            )
        )


class ControlPanelTest(unittest.TestCase):
    def test_twelve_buttons_are_laid_out_on_the_strip(self) -> None:
        self.assertEqual(cad.PANEL_BUTTON_COUNT, 12)
        self.assertEqual(len(cad.PANEL_BUTTON_POSITIONS_MM), 12)
        self.assertEqual(len(set(cad.PANEL_BUTTON_POSITIONS_MM)), 12)

    def test_every_panel_feature_is_on_the_strip_not_the_playing_area(self) -> None:
        strip_far = -cad.PLAYING_SPAN_MM / 2.0 - cad.PANEL_STRIP_DEPTH_MM
        strip_near = -cad.PLAYING_SPAN_MM / 2.0
        radius = cad.PANEL_BUTTON_HOLE_DIAMETER_MM / 2.0
        for x, y in cad.PANEL_BUTTON_POSITIONS_MM:
            self.assertGreaterEqual(y - radius, strip_far)
            self.assertLessEqual(y + radius, strip_near)
            self.assertLess(abs(x) + radius, cad.PLAYING_SPAN_MM / 2.0)
        display_y = cad.PANEL_OLED_CENTER_MM[1]
        half_depth = cad.PANEL_OLED_MODULE_MM[1] / 2.0
        self.assertGreaterEqual(display_y - half_depth, strip_far)
        self.assertLessEqual(display_y + half_depth, strip_near)

    def test_the_display_window_is_smaller_than_its_module(self) -> None:
        for window, module in zip(
            cad.PANEL_OLED_WINDOW_MM, cad.PANEL_OLED_MODULE_MM[:2]
        ):
            self.assertLess(window, module)

    def test_the_panel_and_the_display_do_not_overlap(self) -> None:
        display_x = cad.PANEL_OLED_CENTER_MM[0]
        display_edge = display_x + cad.PANEL_OLED_MODULE_MM[0] / 2.0
        nearest_button = min(x for x, _y in cad.PANEL_BUTTON_POSITIONS_MM)
        button_edge = nearest_button - cad.PANEL_BUTTON_HOLE_DIAMETER_MM / 2.0
        self.assertLess(display_edge, button_edge)


class PlateFixingTest(unittest.TestCase):
    def test_every_plate_screw_lands_on_the_case_ledge(self) -> None:
        """Anywhere further inboard is over the PCB."""
        inner = cad.PLAYING_SPAN_MM / 2.0 - cad.CASE_PLATE_LEDGE_MM
        outer = cad.PLAYING_SPAN_MM / 2.0
        radius = cad.TILE_PLATE_SCREW_HEAD_DIAMETER_MM / 2.0
        for x, y in cad.TILE_PLATE_SCREW_POSITIONS_MM:
            reach = max(abs(x), abs(y))
            with self.subTest(screw=(x, y)):
                self.assertGreaterEqual(reach - radius, inner)
                self.assertLessEqual(reach + radius, outer)

    def test_screws_are_spread_around_the_perimeter(self) -> None:
        self.assertEqual(len(cad.TILE_PLATE_SCREW_POSITIONS_MM), 8)
        self.assertEqual(len(set(cad.TILE_PLATE_SCREW_POSITIONS_MM)), 8)

    def test_screw_heads_sit_below_the_playing_surface(self) -> None:
        self.assertLess(
            cad.TILE_PLATE_SCREW_HEAD_DEPTH_MM, cad.TILE_PLATE_THICKNESS_MM
        )
        self.assertGreater(
            cad.TILE_PLATE_SCREW_HEAD_DIAMETER_MM,
            cad.TILE_PLATE_SCREW_CLEARANCE_DIAMETER_MM,
        )


if __name__ == "__main__":
    unittest.main()
