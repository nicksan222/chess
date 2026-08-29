"""Tests for physical scale and relationships shared by the Blender projects."""

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
            isclose(
                cad.BLENDER_SCALE_LENGTH * cad.MILLIMETRES_PER_METRE,
                1.0,
            )
        )

    def test_finished_span_has_a_plausible_inch_conversion(self) -> None:
        finished_inches = cad.BOARD_FINISHED_SPAN_MM / cad.MILLIMETRES_PER_INCH
        self.assertGreater(finished_inches, 12.0)
        self.assertLess(finished_inches, 16.0)


class ProductScaleTest(unittest.TestCase):
    def test_board_is_explicitly_compact(self) -> None:
        self.assertEqual(cad.BOARD_FORMAT, "compact electronic")
        self.assertGreaterEqual(cad.SQUARE_SIZE_MM, cad.COMPACT_SQUARE_MIN_MM)
        self.assertLessEqual(cad.SQUARE_SIZE_MM, cad.COMPACT_SQUARE_MAX_MM)
        self.assertLess(
            cad.COMPACT_SQUARE_MAX_MM,
            cad.FIDE_REFERENCE_SQUARE_MIN_MM,
        )

    def test_finished_board_cannot_grow_beyond_product_envelope(self) -> None:
        self.assertGreaterEqual(
            cad.BOARD_FINISHED_SPAN_MM,
            cad.COMPACT_BOARD_MIN_SPAN_MM,
        )
        self.assertLessEqual(
            cad.BOARD_FINISHED_SPAN_MM,
            cad.COMPACT_BOARD_MAX_SPAN_MM,
        )
        self.assertLessEqual(
            cad.BOARD_ASSEMBLED_ENVELOPE_MM[2],
            cad.COMPACT_BOARD_MAX_HEIGHT_MM,
        )

    def test_tile_has_a_compact_real_world_envelope(self) -> None:
        self.assertEqual(
            cad.TILE_ASSEMBLED_ENVELOPE_MM,
            (cad.TILE_SIZE_MM, cad.TILE_SIZE_MM, cad.TILE_HEIGHT_MM),
        )
        self.assertGreaterEqual(cad.TILE_HEIGHT_MM, cad.COMPACT_TILE_MIN_HEIGHT_MM)
        self.assertLessEqual(cad.TILE_HEIGHT_MM, cad.COMPACT_TILE_MAX_HEIGHT_MM)

    def test_chessboard_is_eight_square_pitches_across(self) -> None:
        self.assertEqual(cad.GRID_COUNT, 8)
        self.assertTrue(
            isclose(
                cad.PLAYING_SPAN_MM,
                cad.SQUARE_SIZE_MM * cad.GRID_COUNT,
            )
        )

    def test_tile_and_clearance_equal_square_pitch(self) -> None:
        self.assertTrue(
            isclose(
                cad.TILE_SIZE_MM + cad.TILE_EDGE_CLEARANCE_MM,
                cad.SQUARE_SIZE_MM,
            )
        )
        self.assertTrue(
            isclose(
                cad.TILE_EDGE_CLEARANCE_PER_SIDE_MM * 2.0,
                cad.TILE_EDGE_CLEARANCE_MM,
            )
        )


class PrintEnvelopeTest(unittest.TestCase):
    def test_tile_parts_fit_compact_reference_printer(self) -> None:
        self.assertTrue(
            cad.fits_build_volume(
                cad.TILE_PRINTED_PART_ENVELOPE_MM,
                cad.REFERENCE_COMPACT_BUILD_VOLUME_MM,
            )
        )

    def test_empty_board_tray_fits_large_format_printer(self) -> None:
        self.assertEqual(
            cad.BOARD_ASSEMBLED_ENVELOPE_MM,
            (
                cad.BOARD_FINISHED_SPAN_MM,
                cad.BOARD_FINISHED_SPAN_MM,
                cad.BOARD_HEIGHT_MM,
            ),
        )
        self.assertTrue(
            cad.fits_build_volume(
                cad.BOARD_PRINTED_PART_ENVELOPE_MM,
                cad.REFERENCE_LARGE_BUILD_VOLUME_MM,
            )
        )

    def test_metre_scale_error_cannot_fit_reference_printer(self) -> None:
        giant_tile = tuple(axis * 1_000.0 for axis in cad.TILE_PRINTED_PART_ENVELOPE_MM)
        self.assertFalse(
            cad.fits_build_volume(
                giant_tile,
                cad.REFERENCE_COMPACT_BUILD_VOLUME_MM,
            )
        )


class FdmFeatureTest(unittest.TestCase):
    def test_fit_clearances_stay_in_prototype_range(self) -> None:
        for clearance in (
            cad.TILE_EDGE_CLEARANCE_PER_SIDE_MM,
            cad.TILE_LID_CLEARANCE_MM,
        ):
            with self.subTest(clearance=clearance):
                self.assertGreaterEqual(clearance, cad.FDM_MIN_FIT_CLEARANCE_MM)
                self.assertLessEqual(clearance, cad.FDM_MAX_FIT_CLEARANCE_MM)

    def test_structural_features_exceed_minimums(self) -> None:
        features = {
            "bottom wall": cad.TILE_BOTTOM_WALL_MM,
            "lid rail width": cad.TILE_LID_RAIL_WIDTH_MM,
            "lid rail depth": cad.TILE_LID_RAIL_DEPTH_MM,
            "magnet ring": cad.TILE_MAGNET_RING_WIDTH_MM,
            "magnet top skin": cad.TILE_MAGNET_TOP_SKIN_MM,
            "LED top skin": cad.TILE_LED_TOP_SKIN_MM,
            "screw boss": cad.TILE_MOUNT_SCREW_BOSS_DIAMETER_MM,
            "screw clearance hole": cad.TILE_MOUNT_SCREW_CLEARANCE_DIAMETER_MM,
        }
        for name, dimension in features.items():
            with self.subTest(feature=name):
                self.assertGreaterEqual(dimension, cad.FDM_MIN_FEATURE_MM)
        self.assertGreaterEqual(cad.TILE_BOTTOM_FLOOR_MM, cad.FDM_MIN_FLOOR_MM)

    def test_enclosure_halves_equal_assembled_height(self) -> None:
        self.assertTrue(
            isclose(
                cad.TILE_BOTTOM_HEIGHT_MM + cad.TILE_TOP_THICKNESS_MM,
                cad.TILE_HEIGHT_MM,
            )
        )
        self.assertLess(cad.TILE_HEIGHT_MM, 20.0)


class ComponentContainmentTest(unittest.TestCase):
    def test_hidden_magnet_ring_fits_inside_lid(self) -> None:
        self.assertLess(
            cad.MAGNET_RING_INNER_DIAMETER_MM,
            cad.MAGNET_RING_OUTER_DIAMETER_MM,
        )
        self.assertLess(cad.MAGNET_RING_OUTER_DIAMETER_MM, cad.TILE_SIZE_MM)
        self.assertLess(cad.MAGNET_RING_DEPTH_MM, cad.TILE_TOP_THICKNESS_MM)

    def test_led_aperture_and_pocket_fit_inside_tile(self) -> None:
        tile_half = cad.TILE_SIZE_MM / 2.0
        for axis, position in enumerate(cad.LED_POSITION_MM):
            with self.subTest(axis=axis):
                self.assertLessEqual(
                    cad.LED_APERTURE_MM[axis],
                    cad.LED_POCKET_MM[axis],
                )
                pocket_edge = abs(position) + cad.LED_POCKET_MM[axis] / 2.0
                self.assertLessEqual(
                    pocket_edge + cad.TILE_BOTTOM_WALL_MM,
                    tile_half,
                )
                maximum_package = cad.LED_PACKAGE_MAX_SIZE_MM[axis]
                required_pocket = (
                    maximum_package
                    + 2.0 * cad.LED_PACKAGE_CLEARANCE_PER_SIDE_MM
                )
                self.assertGreaterEqual(cad.LED_POCKET_MM[axis], required_pocket)
                self.assertGreaterEqual(
                    cad.LED_APERTURE_MM[axis],
                    cad.LED_EMITTER_WINDOW_MM[axis]
                    + cad.LED_PACKAGE_TOLERANCE_MM,
                )
                self.assertLess(
                    cad.LED_APERTURE_MM[axis],
                    cad.LED_PACKAGE_NOMINAL_SIZE_MM[axis],
                )

        self.assertGreaterEqual(
            cad.LED_POCKET_MM[2],
            cad.LED_PACKAGE_MAX_SIZE_MM[2]
            + cad.LED_PACKAGE_VERTICAL_CLEARANCE_MM,
        )
        self.assertGreaterEqual(cad.TILE_LED_TOP_SKIN_MM, cad.FDM_MIN_FEATURE_MM)

    def test_led_pocket_avoids_magnet_recess_and_lid_rails(self) -> None:
        nearest_pocket_radius = (
            (cad.LED_POSITION_MM[0] - cad.LED_POCKET_MM[0] / 2.0) ** 2
            + (cad.LED_POSITION_MM[1] - cad.LED_POCKET_MM[1] / 2.0) ** 2
        ) ** 0.5
        self.assertGreaterEqual(
            nearest_pocket_radius - cad.MAGNET_RING_OUTER_DIAMETER_MM / 2.0,
            cad.FDM_MIN_FEATURE_MM,
        )

        rail_offset = (
            cad.TILE_LID_RAIL_OUTER_SPAN_MM - cad.TILE_LID_RAIL_WIDTH_MM
        ) / 2.0
        rail_inner_edge = rail_offset - cad.TILE_LID_RAIL_WIDTH_MM / 2.0
        for axis, position in enumerate(cad.LED_POSITION_MM):
            pocket_edge = abs(position) + cad.LED_POCKET_MM[axis] / 2.0
            self.assertGreaterEqual(
                rail_inner_edge - pocket_edge,
                cad.FDM_MIN_FEATURE_MM,
            )

    def test_wired_components_fit_the_tray(self) -> None:
        cavity_half = cad.TILE_INTERNAL_CAVITY_SIZE_MM / 2.0
        self.assertLessEqual(cad.REED_SENSOR_BODY_MM[0] / 2.0, cavity_half)
        for axis, position in enumerate(cad.LED_POSITION_MM):
            pcb_edge = abs(position) + cad.LED_BREAKOUT_PCB_MM[axis] / 2.0
            self.assertLessEqual(pcb_edge, cavity_half)
        self.assertGreaterEqual(
            cad.TILE_WIRE_PORT_WIDTH_MM,
            3.0 * cad.ELECTRONICS_WIRE_DIAMETER_MM,
        )

    def test_wire_port_remains_inside_tray_wall_height(self) -> None:
        port_bottom = (
            cad.TILE_WIRE_PORT_CENTER_Z_MM - cad.TILE_WIRE_PORT_HEIGHT_MM / 2.0
        )
        port_top = (
            cad.TILE_WIRE_PORT_CENTER_Z_MM + cad.TILE_WIRE_PORT_HEIGHT_MM / 2.0
        )
        self.assertGreaterEqual(port_bottom, cad.TILE_BOTTOM_FLOOR_MM)
        self.assertLessEqual(port_top, cad.TILE_BOTTOM_HEIGHT_MM)


class SkeletonRelationshipTest(unittest.TestCase):
    def test_empty_tray_frame_and_floor_match_tile_grid(self) -> None:
        self.assertTrue(
            isclose(
                cad.BOARD_FINISHED_SPAN_MM,
                cad.PLAYING_SPAN_MM + 2.0 * cad.BOARD_FRAME_WIDTH_MM,
            )
        )
        self.assertTrue(
            isclose(
                cad.BOARD_HEIGHT_MM,
                cad.BOARD_FLOOR_THICKNESS_MM + cad.TILE_HEIGHT_MM,
            )
        )
        self.assertEqual(
            cad.BOARD_TRAY_CAVITY_SIZE_MM[:2],
            (cad.PLAYING_SPAN_MM, cad.PLAYING_SPAN_MM),
        )

    def test_velcro_pockets_leave_a_printable_floor(self) -> None:
        self.assertEqual(len(cad.TILE_VELCRO_PAD_POSITIONS_MM), 4)
        remaining_floor = cad.TILE_BOTTOM_FLOOR_MM - cad.TILE_VELCRO_PAD_DEPTH_MM
        self.assertGreaterEqual(remaining_floor, cad.FDM_MIN_FLOOR_MM)

    def test_optional_screws_have_reinforced_bearing_bosses(self) -> None:
        self.assertEqual(len(cad.TILE_MOUNT_SCREW_POSITIONS_MM), 2)
        self.assertGreater(
            cad.TILE_MOUNT_SCREW_HEAD_DIAMETER_MM,
            cad.TILE_MOUNT_SCREW_CLEARANCE_DIAMETER_MM,
        )
        self.assertGreater(
            cad.TILE_MOUNT_SCREW_BOSS_DIAMETER_MM,
            cad.TILE_MOUNT_SCREW_HEAD_DIAMETER_MM,
        )
        self.assertGreater(
            cad.TILE_MOUNT_SCREW_BOSS_HEIGHT_MM,
            cad.TILE_MOUNT_SCREW_HEAD_DEPTH_MM,
        )
        self.assertLess(
            cad.BOARD_MOUNT_SCREW_PILOT_DIAMETER_MM,
            cad.TILE_MOUNT_SCREW_CLEARANCE_DIAMETER_MM,
        )
        self.assertLess(
            cad.BOARD_MOUNT_SCREW_PILOT_DEPTH_MM,
            cad.BOARD_FLOOR_THICKNESS_MM,
        )


class CompositionLedAlignmentTest(unittest.TestCase):
    def test_every_tile_led_is_inside_and_aligned_in_the_composition(self) -> None:
        expected_addresses = {
            (row, column)
            for row in range(cad.GRID_COUNT)
            for column in range(cad.GRID_COUNT)
        }
        board_leds = {
            (row, column): (x, y)
            for row, column, x, y in cad.BOARD_LED_POSITIONS_MM
        }
        self.assertEqual(len(expected_addresses), 64)
        self.assertEqual(set(board_leds), expected_addresses)
        self.assertEqual(len(set(board_leds.values())), 64)

        grid_half = cad.PLAYING_SPAN_MM / 2.0
        for row, column in sorted(expected_addresses):
            tile_center_x = -grid_half + (column + 0.5) * cad.SQUARE_SIZE_MM
            tile_center_y = grid_half - (row + 0.5) * cad.SQUARE_SIZE_MM
            expected_led = (
                tile_center_x + cad.LED_POSITION_MM[0],
                tile_center_y + cad.LED_POSITION_MM[1],
            )
            actual_led = board_leds[(row, column)]
            with self.subTest(row=row, column=column):
                self.assertTrue(isclose(expected_led[0], actual_led[0], abs_tol=1e-9))
                self.assertTrue(isclose(expected_led[1], actual_led[1], abs_tol=1e-9))
                self.assertLessEqual(abs(actual_led[0]), grid_half)
                self.assertLessEqual(abs(actual_led[1]), grid_half)


class CompositionHoleAlignmentTest(unittest.TestCase):
    def test_every_tile_screw_hole_aligns_with_its_board_pilot(self) -> None:
        expected_addresses = {
            (row, column, screw_index)
            for row in range(cad.GRID_COUNT)
            for column in range(cad.GRID_COUNT)
            for screw_index in range(len(cad.TILE_MOUNT_SCREW_POSITIONS_MM))
        }
        board_pilots = {
            (row, column, screw_index): (x, y)
            for row, column, screw_index, x, y in (
                cad.BOARD_MOUNT_SCREW_PILOT_POSITIONS_MM
            )
        }

        self.assertEqual(len(expected_addresses), 128)
        self.assertEqual(set(board_pilots), expected_addresses)
        self.assertEqual(len(board_pilots), 128)
        self.assertEqual(len(set(board_pilots.values())), 128)

        grid_half = cad.PLAYING_SPAN_MM / 2.0
        for row, column, screw_index in sorted(expected_addresses):
            tile_center_x = (
                -grid_half + (column + 0.5) * cad.SQUARE_SIZE_MM
            )
            tile_center_y = grid_half - (row + 0.5) * cad.SQUARE_SIZE_MM
            local_x, local_y = cad.TILE_MOUNT_SCREW_POSITIONS_MM[screw_index]
            tile_hole = (tile_center_x + local_x, tile_center_y + local_y)
            board_hole = board_pilots[(row, column, screw_index)]

            with self.subTest(
                row=row,
                column=column,
                screw_index=screw_index,
            ):
                self.assertTrue(isclose(tile_hole[0], board_hole[0], abs_tol=1e-9))
                self.assertTrue(isclose(tile_hole[1], board_hole[1], abs_tol=1e-9))


if __name__ == "__main__":
    unittest.main()
