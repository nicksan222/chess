"""Tests for shared board wiring and coordinate mappings."""

import unittest

from shared import dimensions, wiring


class WiringTest(unittest.TestCase):
    def test_files_match_board_width(self):
        self.assertEqual(len(wiring.FILES), dimensions.GRID_COUNT)

    def test_square_names_round_trip(self):
        for rank in range(dimensions.GRID_COUNT):
            for file_index in range(dimensions.GRID_COUNT):
                position = (file_index, rank)
                self.assertEqual(
                    wiring.parse_square(wiring.square(*position)), position
                )

    def test_square_mappings_are_bijective(self):
        positions = [
            (file_index, rank)
            for rank in range(dimensions.GRID_COUNT)
            for file_index in range(dimensions.GRID_COUNT)
        ]
        self.assertEqual(
            len({wiring.expander_of(*p) for p in positions}), len(positions)
        )
        self.assertEqual(len(wiring.led_chain_order()), len(positions))


if __name__ == "__main__":
    unittest.main()
