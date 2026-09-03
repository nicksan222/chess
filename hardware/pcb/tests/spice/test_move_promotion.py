"""Promotion: explicit actions and electrical checks."""

import unittest

from spice.movement import MovementCase
from spice.support import board_circuits, run_circuit


class PromotionSpiceTest(unittest.TestCase):
    def test_promotion_rank_transition_is_visible(self) -> None:
        case = (
            MovementCase("promotion")
            .starts_with("A7")
            .expect_occupied("pawn_initial", "A7", at_ms=0.25)
            .expect_empty("promotion_square_initial", "A8", at_ms=0.25)
            .lift("A7", at_ms=1)
            .expect_empty("pawn_lifted", "A7", at_ms=1.25)
            .place("A8", at_ms=2)
            .expect_occupied("promoted_piece_placed", "A8", at_ms=2.25)
        )
        circuit = board_circuits().movement(case)
        run_circuit(__file__, circuit)


if __name__ == "__main__":
    unittest.main()
