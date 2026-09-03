"""Open main-power-switch capability."""

import unittest

from spice.support import board_circuits, run_circuit


class PowerOffSpiceTest(unittest.TestCase):
    def test_open_switch_removes_the_board_rail(self) -> None:
        circuit = board_circuits().power_off().clear_expectations()
        circuit.expect("5v", 0.0, 0.01)
        run_circuit(__file__, circuit)


if __name__ == "__main__":
    unittest.main()
