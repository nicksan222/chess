"""Signals scenarios against the native board connectivity."""

from __future__ import annotations

import unittest

from spice.electrical import AHCT125, LOGIC_3V3
from spice.support import board_circuits, run_circuit


class SignalSpiceTest(unittest.TestCase):
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
        run_circuit("test_buttons.py", circuit)

    def test_every_square_detects_a_piece_at_valid_gpio_voltage(self) -> None:
        circuit = board_circuits().all_squares().clear_expectations()
        for file_name in "abcdefgh":
            for rank in range(1, 9):
                circuit.expect(f"{file_name}{rank}", *LOGIC_3V3.low.tuple())
        run_circuit("test_hall_all_squares.py", circuit)

    def test_both_ahct125_channels_reach_valid_led_logic_levels(self) -> None:
        circuit = board_circuits().level_shifter().clear_expectations()
        circuit.expect("channel_1", *AHCT125.low.tuple())
        circuit.expect("channel_2", *AHCT125.high.tuple())
        run_circuit("test_level_shifter.py", circuit)

    def test_each_bus_reaches_valid_released_and_asserted_levels(self) -> None:
        circuit = board_circuits().open_drain_inputs().clear_expectations()
        for signal in ("i2c_sda", "i2c_scl"):
            circuit.expect(f"{signal}_released", *LOGIC_3V3.high.tuple())
            circuit.expect(f"{signal}_low", *LOGIC_3V3.low.tuple())
        run_circuit("test_open_drain_inputs.py", circuit)
