"""SPI level-shifter electrical capability."""

import unittest

from components.electrical import AHCT125
from spice.support import board_circuits, run_circuit


class LevelShifterSpiceTest(unittest.TestCase):
    def test_both_ahct125_channels_reach_valid_led_logic_levels(self) -> None:
        circuit = board_circuits().level_shifter().clear_expectations()
        circuit.expect("channel_1", *AHCT125.low.tuple())
        circuit.expect("channel_2", *AHCT125.high.tuple())
        run_circuit(__file__, circuit)


if __name__ == "__main__":
    unittest.main()
