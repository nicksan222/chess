"""Ordinary movement: explicit actions and electrical checks."""

import unittest

from spice.movement import MovementCase
from spice.support import board_circuits, run_circuit


class QuietMoveSpiceTest(unittest.TestCase):
    def test_lift_then_place_is_electrically_visible(self) -> None:
        case = (
            MovementCase("quiet")
            .starts_with("A2")
            .expect_occupied("origin_before_lift", "A2", at_ms=0.25)
            .expect_empty("target_before_move", "A4", at_ms=0.25)
            .lift("A2", at_ms=1)
            .expect_empty("origin_after_lift", "A2", at_ms=1.25)
            .place("A4", at_ms=2)
            .expect_occupied("target_after_place", "A4", at_ms=2.25)
        )
        circuit = board_circuits().movement(case)
        run_circuit(__file__, circuit)


if __name__ == "__main__":
    unittest.main()
