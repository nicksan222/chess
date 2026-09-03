"""Unsafe unrestricted LED load detection."""

import unittest

from spice.support import board_circuits, run_circuit


class FullWhitePowerSpiceTest(unittest.TestCase):
    def test_full_white_exposes_supply_sag_and_overcurrent(self) -> None:
        circuit = board_circuits().power(full_white=True).clear_expectations()
        circuit.expect("current", 4.28, 4.30)
        circuit.expect("5v", 4.30, 4.63)
        run_circuit(__file__, circuit)


if __name__ == "__main__":
    unittest.main()
