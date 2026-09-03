"""I2C and shared-interrupt electrical capability."""

import unittest

from components.electrical import LOGIC_3V3
from spice.support import board_circuits, run_circuit


class OpenDrainInputSpiceTest(unittest.TestCase):
    def test_each_bus_reaches_valid_released_and_asserted_levels(self) -> None:
        circuit = board_circuits().open_drain_inputs().clear_expectations()
        for signal in ("i2c_sda", "i2c_scl", "sense_irq"):
            circuit.expect(f"{signal}_released", *LOGIC_3V3.high.tuple())
            circuit.expect(f"{signal}_low", *LOGIC_3V3.low.tuple())
        run_circuit(__file__, circuit)


if __name__ == "__main__":
    unittest.main()
