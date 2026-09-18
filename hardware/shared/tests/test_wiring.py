"""Tests for shared board wiring and coordinate mappings."""

import unittest

from shared import dimensions, wiring
from shared.hall_banks import FILES, SquarePosition


class WiringTest(unittest.TestCase):
    def test_files_match_board_width(self):
        self.assertEqual(len(FILES), dimensions.GRID_COUNT)

    def test_square_names_round_trip(self):
        for rank in range(dimensions.GRID_COUNT):
            for file_index in range(dimensions.GRID_COUNT):
                position = SquarePosition(file_index, rank)
                self.assertEqual(wiring.parse_square(position.name), position)

    def test_square_position_rejects_invalid_names_and_coordinates(self):
        for name in ("", "I1", "A0", "A9", "Afoo"):
            with (
                self.subTest(name=name),
                self.assertRaisesRegex(ValueError, "invalid square"),
            ):
                wiring.parse_square(name)
        with self.assertRaisesRegex(ValueError, "invalid square coordinates"):
            SquarePosition(-1, 0)

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
            self.assertEqual(len({position.file_index for position in bank.members}), 4)
            self.assertEqual(len({position.rank for position in bank.members}), 2)
            self.assertEqual(
                sum(int(high) << bit for bit, high in enumerate(bank.straps)),
                bank.index,
            )

    def test_square_mappings_are_bijective(self):
        positions = [
            SquarePosition(file_index, rank)
            for rank in range(dimensions.GRID_COUNT)
            for file_index in range(dimensions.GRID_COUNT)
        ]
        self.assertEqual(
            len({wiring.expander_of(position) for position in positions}),
            len(positions),
        )
        chain = wiring.led_chain_order()
        self.assertEqual(len(chain), len(positions))
        self.assertEqual(
            [position.name for position in chain[:9]],
            ["A1", "B1", "C1", "D1", "E1", "F1", "G1", "H1", "H2"],
        )

    def test_expander_assignment_has_named_fields(self):
        assignment = wiring.expander_of(wiring.parse_square("C2"))

        self.assertEqual(assignment.bank, dimensions.HALL_BANKS[0])
        self.assertEqual(assignment.pin_index, 6)


if __name__ == "__main__":
    unittest.main()
