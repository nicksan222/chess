"""Approved LED brightness power capability."""

import unittest

from components.electrical import BOARD_POWER
from spice.support import board_circuits, run_circuit


class ApprovedPowerSpiceTest(unittest.TestCase):
    def test_approved_brightness_keeps_current_and_voltage_safe(self) -> None:
        board = board_circuits()
        expected_current = board.power_current()
        circuit = board.power().clear_expectations()
        circuit.expect(
            "current",
            expected_current - BOARD_POWER.current_tolerance_amps,
            expected_current + BOARD_POWER.current_tolerance_amps,
        )
        circuit.expect("5v", *BOARD_POWER.healthy_rail.tuple())
        run_circuit(__file__, circuit)


if __name__ == "__main__":
    unittest.main()
