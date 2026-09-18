"""Tests for the cohesive physical-square layout."""

import unittest

from shared import dimensions
from shared.hall_banks import SquarePosition


class SquareLayoutTest(unittest.TestCase):
    def test_all_published_electrical_identities_are_stable(self) -> None:
        expected_led_order = """
            A1 B1 C1 D1 E1 F1 G1 H1 H2 G2 F2 E2 D2 C2 B2 A2
            A3 B3 C3 D3 E3 F3 G3 H3 H4 G4 F4 E4 D4 C4 B4 A4
            A5 B5 C5 D5 E5 F5 G5 H5 H6 G6 F6 E6 D6 C6 B6 A6
            A7 B7 C7 D7 E7 F7 G7 H7 H8 G8 F8 E8 D8 C8 B8 A8
        """.split()  # noqa: SIM905 - compact, reviewable golden data
        expected_sensor_order = """
            A1 B1 C1 D1 A2 B2 C2 D2 A3 B3 C3 D3 A4 B4 C4 D4
            E1 F1 G1 H1 E2 F2 G2 H2 E3 F3 G3 H3 E4 F4 G4 H4
            A5 B5 C5 D5 A6 B6 C6 D6 A7 B7 C7 D7 A8 B8 C8 D8
            E5 F5 G5 H5 E6 F6 G6 H6 E7 F7 G7 H7 E8 F8 G8 H8
        """.split()  # noqa: SIM905 - compact, reviewable golden data

        self.assertEqual(
            [square.name for square in dimensions.BOARD_SQUARES.led_chain],
            expected_led_order,
        )
        self.assertEqual(
            [
                dimensions.BOARD_SQUARES.by_position(
                    SquarePosition.parse(name)
                ).sensor_number
                for name in expected_sensor_order
            ],
            list(range(1, 65)),
        )

    def test_checkerboard_phase_is_stable(self) -> None:
        expected_dark_names = """
            A1 C1 E1 G1 B2 D2 F2 H2 A3 C3 E3 G3 B4 D4 F4 H4
            A5 C5 E5 G5 B6 D6 F6 H6 A7 C7 E7 G7 B8 D8 F8 H8
        """.split()  # noqa: SIM905 - compact, reviewable golden data

        self.assertEqual(
            sorted(square.name for square in dimensions.BOARD_SQUARES.dark_squares),
            sorted(expected_dark_names),
        )
        self.assertTrue(dimensions.BOARD_SQUARES.by_name("A1").is_dark)
        self.assertFalse(dimensions.BOARD_SQUARES.by_name("A2").is_dark)
        self.assertFalse(dimensions.BOARD_SQUARES.by_name("B1").is_dark)
