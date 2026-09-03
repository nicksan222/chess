"""Complete control-button electrical capability."""

import unittest

from components.electrical import LOGIC_3V3
from spice.support import board_circuits, run_circuit


class ButtonBankSpiceTest(unittest.TestCase):
    def test_all_twelve_pressed_buttons_reach_valid_gpio_low(self) -> None:
        circuit = board_circuits().buttons().clear_expectations()
        for button in (
            "btn_up",
            "btn_down",
            "btn_left",
            "btn_right",
            "btn_ok",
            "btn_reset",
            "btn_pass",
            "btn_f1",
            "btn_f2",
            "btn_f3",
            "btn_f4",
            "btn_f5",
        ):
            circuit.expect(button, *LOGIC_3V3.low.tuple())
        run_circuit(__file__, circuit)


if __name__ == "__main__":
    unittest.main()
