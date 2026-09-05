"""Unsafe unrestricted LED load detection."""

import unittest

from components.electrical import BOARD_POWER
from spice.support import board_circuits, run_circuit


class FullWhitePowerSpiceTest(unittest.TestCase):
    def test_full_white_exposes_supply_sag_and_overcurrent(self) -> None:
        board = board_circuits()
        expected_current = board.power_current(full_white=True)
        circuit = board.power(full_white=True).clear_expectations()
        circuit.expect(
            "current",
            expected_current - BOARD_POWER.current_tolerance_amps,
            expected_current + BOARD_POWER.current_tolerance_amps,
        )
        circuit.expect("5v", *BOARD_POWER.overloaded_rail.tuple())
        run_circuit(__file__, circuit)


if __name__ == "__main__":
    unittest.main()
