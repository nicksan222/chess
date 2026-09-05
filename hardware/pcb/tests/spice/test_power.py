"""Power scenarios against the native board connectivity."""

from __future__ import annotations

import unittest

from spice.electrical import BOARD_POWER
from spice.support import board_circuits, run_circuit


class PowerSpiceTest(unittest.TestCase):
    def test_approved_brightness_keeps_current_and_voltage_safe(self) -> None:
        board = board_circuits()
        expected_current = board.power_current()
        circuit = board.power().clear_expectations()
        circuit.expect(
            "current",
            expected_current - BOARD_POWER.current_tolerance_amps,
            expected_current + BOARD_POWER.current_tolerance_amps,
        )
        circuit.expect("5v", *BOARD_POWER.healthy_rail.tuple())
        run_circuit("test_power_approved.py", circuit)

    def test_full_white_exposes_supply_sag_and_overcurrent(self) -> None:
        board = board_circuits()
        expected_current = board.power_current(full_white=True)
        circuit = board.power(full_white=True).clear_expectations()
        circuit.expect(
            "current",
            expected_current - BOARD_POWER.current_tolerance_amps,
            expected_current + BOARD_POWER.current_tolerance_amps,
        )
        circuit.expect("5v", *BOARD_POWER.overloaded_rail.tuple())
        run_circuit("test_power_full_white.py", circuit)

    def test_open_switch_removes_the_board_rail(self) -> None:
        circuit = board_circuits().power_off().clear_expectations()
        circuit.expect("5v", *BOARD_POWER.off_rail.tuple())
        run_circuit("test_power_off.py", circuit)

    def test_rail_settles_after_switch_on_with_every_fitted_capacitor(self) -> None:
        circuit = board_circuits().power_startup().clear_expectations()
        circuit.expect("5v_at_1ms", *BOARD_POWER.healthy_rail.tuple())
        run_circuit("test_power_startup.py", circuit)
