"""Fitted-capacitor startup capability."""

import unittest

from spice.support import board_circuits, run_circuit


class PowerStartupSpiceTest(unittest.TestCase):
    def test_rail_settles_after_switch_on_with_every_fitted_capacitor(self) -> None:
        circuit = board_circuits().power_startup().clear_expectations()
        circuit.expect("5v_at_1ms", 4.75, 5.1)
        run_circuit(__file__, circuit)


if __name__ == "__main__":
    unittest.main()
