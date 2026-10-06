"""Signal scenarios on the native board.

Connectivity checks (ideal switches, `electrical.py` pass bands): one button
press or bus driver reaches its own net only. Datasheet-limited checks: Hall
output levels at the 3.3 V corners and LED data/clock levels at the 4.5/5.5 V
corners.
"""

from __future__ import annotations

import unittest

from spice import datasheets
from spice.electrical import LOGIC_3V3
from spice.support import board_circuits, run_circuit


class SignalSpiceTest(unittest.TestCase):
    """Signal levels from the real board: buttons, Hall outputs, level shifter and open-drain buses."""

    def test_each_button_alone_pulls_only_its_own_gpio_low(self) -> None:
        # Connectivity: TL1105 contact resistance against the Pi's strongest
        # pull-up, with an ideal 3.3 V rail and press timing.
        circuit = board_circuits().buttons().clear_expectations()
        buttons = (
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
        )
        for button in buttons:
            circuit.expect(f"{button}_idle", *LOGIC_3V3.high.tuple())
            for pressed in buttons:
                level = LOGIC_3V3.low if pressed == button else LOGIC_3V3.high
                circuit.expect(f"{button}_with_{pressed}", *level.tuple())
        run_circuit("test_buttons.py", circuit)

    def test_every_square_reads_low_with_a_magnet_and_high_without(self) -> None:
        # DRV5032 VOL 0.3 V at 1 mA vs the strongest TCA9554 pull-up (IIL 100 uA);
        # leakage (DRV IOZ + TCA IIH) vs the typical 100 k pull-up; 3.3 V +-5 %.
        board = board_circuits()
        for vcc in (datasheets.RAIL_3V3_VOLTS.low, datasheets.RAIL_3V3_VOLTS.high):
            for occupied in (True, False):
                state = "occupied" if occupied else "empty"
                with self.subTest(vcc=vcc, state=state):
                    circuit = board.hall_levels(occupied=occupied, vcc=vcc)
                    self.assertEqual(len(circuit.expectations), 64)
                    run_circuit(f"test_hall_{state}_{vcc:.3f}.py", circuit)

    def test_led_data_and_clock_levels_hold_at_the_rail_corners(self) -> None:
        # Pi VOH/VOL -> AHCT125 VIH/VIL, AHCT125 datasheet VOH/VOL -> SK9822
        # 0.7/0.3 x VDD, at the 4.5 and 5.5 V ends of both parts' supply range.
        board = board_circuits()
        for vcc in (datasheets.AHCT125_VCC.low, datasheets.AHCT125_VCC.high):
            for high in (True, False):
                with self.subTest(vcc=vcc, high=high):
                    circuit = board.level_shifter(vcc=vcc, high=high)
                    self.assertEqual(len(circuit.expectations), 4)
                    level = "high" if high else "low"
                    run_circuit(f"test_level_shift_{level}_{vcc:g}.py", circuit)

    def test_each_bus_input_connects_to_its_pull_up_and_driver(self) -> None:
        # Connectivity: an ideal 50 Ohm driver against the Pi's pull-ups; the
        # datasheet bus edges and VOL are in test_i2c.
        circuit = board_circuits().open_drain_inputs().clear_expectations()
        for signal in ("i2c_sda", "i2c_scl"):
            circuit.expect(f"{signal}_released", *LOGIC_3V3.high.tuple())
            circuit.expect(f"{signal}_low", *LOGIC_3V3.low.tuple())
        run_circuit("test_open_drain_inputs.py", circuit)
