"""Negative checks on the shared locating interface for future printed pieces."""

import unittest
from unittest.mock import patch

from shared import dimensions
from shared.dimensions import validation


class PieceSeatsTest(unittest.TestCase):
    def test_foot_has_side_and_floor_clearance(self) -> None:
        self.assertGreater(
            dimensions.TILE_PLATE_PIECE_SEAT_DEPTH_MM,
            dimensions.PIECE_LOCATING_FOOT_HEIGHT_MM,
        )
        self.assertGreater(
            dimensions.TILE_PLATE_PIECE_SEAT_SIDE_MM,
            dimensions.PIECE_LOCATING_FOOT_SIDE_MM,
        )
        validation.validate_piece_seats()

    def test_deep_seat_cannot_break_the_sensor_cover(self) -> None:
        with (
            patch.object(validation, "TILE_PLATE_PIECE_SEAT_DEPTH_MM", 2.0),
            self.assertRaisesRegex(ValueError, "solid floor"),
        ):
            validation.validate_piece_seats()

    def test_foot_cannot_bottom_out_before_its_base_is_seated(self) -> None:
        with (
            patch.object(validation, "PIECE_LOCATING_FOOT_HEIGHT_MM", 0.9),
            self.assertRaisesRegex(ValueError, "bottoming out"),
        ):
            validation.validate_piece_seats()

    def test_thin_support_wall_is_rejected(self) -> None:
        with (
            patch.object(validation, "TILE_PLATE_PIECE_SEAT_SUPPORT_SIDE_MM", 18.5),
            self.assertRaisesRegex(ValueError, "reinforced"),
        ):
            validation.validate_piece_seats()

    def test_lowered_control_strip_preserves_button_relief_floor(self) -> None:
        with (
            patch.object(validation, "PANEL_SURFACE_RECESS_MM", 1.5),
            self.assertRaisesRegex(ValueError, "protrude|floor|bezel"),
        ):
            validation.validate_buttons()

    def test_ring_foot_cannot_collide_with_the_center_island(self) -> None:
        with (
            patch.object(validation, "PIECE_LOCATING_FOOT_INNER_SIDE_MM", 13.5),
            self.assertRaisesRegex(ValueError, "center island"),
        ):
            validation.validate_piece_seats()

    def test_ring_channel_cannot_be_a_solid_square_hole(self) -> None:
        with (
            patch.object(validation, "TILE_PLATE_PIECE_SEAT_INNER_SIDE_MM", 0.0),
            self.assertRaisesRegex(ValueError, "center island"),
        ):
            validation.validate_piece_seats()

    def test_button_cap_cannot_float_above_its_stem(self) -> None:
        with (
            patch.object(validation, "PANEL_BUTTON_CAP_BOTTOM_Z_MM", 32.0),
            self.assertRaisesRegex(ValueError, "engage"),
        ):
            validation.validate_buttons()

    def test_button_cap_socket_must_have_print_clearance(self) -> None:
        with (
            patch.object(validation, "PANEL_BUTTON_CAP_SOCKET_DIAMETER_MM", 3.8),
            self.assertRaisesRegex(ValueError, "cap socket"),
        ):
            validation.validate_buttons()

    def test_display_mounting_pilot_retains_its_floor(self) -> None:
        with (
            patch.object(validation, "PANEL_OLED_PILOT_FLOOR_MM", 0.5),
            self.assertRaisesRegex(ValueError, "printable floor"),
        ):
            validation.validate()
