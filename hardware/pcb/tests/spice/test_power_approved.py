"""Approved LED brightness power capability."""

import unittest

from spice.support import board_circuits, run_circuit


class ApprovedPowerSpiceTest(unittest.TestCase):
    def test_approved_brightness_keeps_current_and_voltage_safe(self) -> None:
        circuit = board_circuits().power().clear_expectations()
        circuit.expect("current", 0.81, 0.84)
        circuit.expect("5v", 4.75, 5.1)
        run_circuit(__file__, circuit)


if __name__ == "__main__":
    unittest.main()
