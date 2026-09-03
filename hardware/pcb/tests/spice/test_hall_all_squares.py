"""Exhaustive 64-square Hall sensor capability."""

import unittest

from spice.support import board_circuits, run_circuit


class AllSquareHallSpiceTest(unittest.TestCase):
    def test_every_square_detects_a_piece_at_valid_gpio_voltage(self) -> None:
        circuit = board_circuits().all_squares().clear_expectations()
        for file_name in "abcdefgh":
            for rank in range(1, 9):
                circuit.expect(f"{file_name}{rank}", 0.0, 0.1)
        run_circuit(__file__, circuit)


if __name__ == "__main__":
    unittest.main()
