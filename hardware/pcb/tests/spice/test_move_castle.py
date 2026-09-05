"""Castling: explicit king/rook actions and electrical checks."""

import unittest

from spice.movement import MovementCase
from spice.support import board_circuits, run_circuit


class CastleSpiceTest(unittest.TestCase):
    def test_king_and_rook_transitions_are_visible(self) -> None:
        case = (
            MovementCase("castle")
            .starts_with("E1", "H1")
            .expect_occupied("king_initial", "E1", at_ms=0.25)
            .expect_occupied("rook_initial", "H1", at_ms=0.25)
            .expect_empty("king_destination_initial", "G1", at_ms=0.25)
            .expect_empty("rook_destination_initial", "F1", at_ms=0.25)
            .lift("E1", at_ms=1)
            .expect_empty("king_lifted", "E1", at_ms=1.25)
            .place("G1", at_ms=2)
            .expect_occupied("king_placed", "G1", at_ms=2.25)
            .lift("H1", at_ms=3)
            .expect_empty("rook_lifted", "H1", at_ms=3.25)
            .place("F1", at_ms=4)
            .expect_occupied("rook_placed", "F1", at_ms=4.25)
        )
        circuit = board_circuits().movement(case)
        run_circuit(__file__, circuit)


if __name__ == "__main__":
    unittest.main()
