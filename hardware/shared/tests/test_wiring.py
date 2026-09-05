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

    def test_compact_banks_cover_all_inputs_and_addresses(self):
        banks = dimensions.HALL_BANKS
        self.assertEqual(len(banks), 8)
        members = [member for bank in banks for member in bank.members]
        self.assertEqual(len(members), 64)
        self.assertEqual(len(set(members)), 64)
        self.assertEqual({bank.address for bank in banks}, set(range(0x20, 0x28)))
        self.assertNotIn(wiring.OLED_ADDRESS, {bank.address for bank in banks})
        for bank in banks:
            self.assertEqual(len(bank.members), 8)
            self.assertEqual(len({file for file, _rank in bank.members}), 4)
            self.assertEqual(len({rank for _file, rank in bank.members}), 2)
            self.assertEqual(
                sum(int(high) << bit for bit, high in enumerate(bank.straps)),
                bank.index,
            )
            self.assertEqual(
                [pin for pin, _name in wiring.expander_squares(bank.index)],
                list(range(8)),
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
