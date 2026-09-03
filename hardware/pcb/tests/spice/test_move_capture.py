"""Capture: explicit actions and electrical checks."""

import unittest

from spice.movement import MovementCase
from spice.support import board_circuits, run_circuit


class CaptureSpiceTest(unittest.TestCase):
    def test_captured_piece_and_attacker_transitions_are_visible(self) -> None:
        case = (
            MovementCase("capture")
            .starts_with("E4", "D5")
            .expect_occupied("attacker_initial", "E4", at_ms=0.25)
            .expect_occupied("victim_initial", "D5", at_ms=0.25)
            .lift("D5", at_ms=1)
            .expect_empty("victim_removed", "D5", at_ms=1.25)
            .lift("E4", at_ms=2)
            .expect_empty("attacker_lifted", "E4", at_ms=2.25)
            .place("D5", at_ms=3)
            .expect_occupied("attacker_placed", "D5", at_ms=3.25)
        )
        circuit = board_circuits().movement(case)
        run_circuit(__file__, circuit)


if __name__ == "__main__":
    unittest.main()
