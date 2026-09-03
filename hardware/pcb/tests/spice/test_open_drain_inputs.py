"""I2C and shared-interrupt electrical capability."""

import unittest

from spice.support import board_circuits, run_circuit


class OpenDrainInputSpiceTest(unittest.TestCase):
    def test_each_bus_reaches_valid_released_and_asserted_levels(self) -> None:
        circuit = board_circuits().open_drain_inputs().clear_expectations()
        for signal in ("i2c_sda", "i2c_scl", "sense_irq"):
            circuit.expect(f"{signal}_released", 3.2, 3.4)
            circuit.expect(f"{signal}_low", 0.0, 0.1)
        run_circuit(__file__, circuit)


if __name__ == "__main__":
    unittest.main()
