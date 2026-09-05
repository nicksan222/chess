"""En passant: explicit three-square actions and electrical checks."""

import unittest

from spice.movement import MovementCase
from spice.support import board_circuits, run_circuit


class EnPassantSpiceTest(unittest.TestCase):
    def test_three_square_transition_is_visible(self) -> None:
        case = (
            MovementCase("en-passant")
            .starts_with("E5", "D5")
            .expect_occupied("attacker_initial", "E5", at_ms=0.25)
            .expect_occupied("victim_initial", "D5", at_ms=0.25)
            .expect_empty("destination_initial", "D6", at_ms=0.25)
            .lift("E5", at_ms=1)
            .expect_empty("attacker_lifted", "E5", at_ms=1.25)
            .lift("D5", at_ms=2)
            .expect_empty("victim_removed", "D5", at_ms=2.25)
            .place("D6", at_ms=3)
            .expect_occupied("destination_filled", "D6", at_ms=3.25)
        )
        circuit = board_circuits().movement(case)
        run_circuit(__file__, circuit)


if __name__ == "__main__":
    unittest.main()
