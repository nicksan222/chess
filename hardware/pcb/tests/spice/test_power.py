"""Power scenarios at datasheet corners against the native board (S4/S4b).

Supply path and plane drop are modelled from the routed board; the U74 eFuse is a
behavioural [BEH] model of TI SLVSFC9C (`efuse_model.py`). Assertions are margins
against limits from the parts' own datasheets (`datasheets.py`), not re-derived
equalities.
"""

from __future__ import annotations

import unittest

from spice import datasheets
from spice.circuit import SpiceCircuit
from spice.efuse_model import Corner, EfuseBoard, slew
from spice.plane_mesh import PlaneMesh, routed_board
from spice.power_path import FUSES, pick, series_path
from spice.power_path import Corner as PathCorner
from spice.residuals import residual
from spice.support import board_circuits, run_circuit

# Board rule: the +5V/GND planes may lose at most 50 mV between the supply entry
# and any LED (1 % of 5 V); the source path is budgeted by the corner test below.
PLANE_DROP_BUDGET_VOLTS = 0.050
# Residual of the OVLO filter (S4c, ASSUMPTION "OVLO filter"): when a running supply
# steps to 6-7 V, [BEH] at the slowest trip corner gives a trip after 1.72 / 0.65 ms,
# a rail peak of 5.99 / 6.03 V and 10.5 / 10.0 ms above 5.5 V with only the LEDs'
# static load (the bulk capacitors hold the rail after the trip). Bounds about 10 %
# above those values, so a change that worsens the residual fails.
RUNNING_STEP_TRIP_MS = 2.0
RUNNING_STEP_PEAK_VOLTS = 6.1
RUNNING_STEP_OVER_MS = 12.0
SQUARES = [f"{file}{rank}" for file in "abcdefgh" for rank in range(1, 9)]


def _led_amps(brightness: float) -> float:
    """LED chain current (amps) at a global brightness fraction: static current plus three channels at the datasheet maximum."""
    return (
        datasheets.SK9822_STATIC_AMPS
        + 3 * datasheets.SK9822_CHANNEL_AMPS_MAX * brightness
    )


def _fuse_mpn() -> str:
    """MPN of the fitted input fuse (F1), so the fuse limits come from the board."""
    return board_circuits().components["F1"].GetValue()


def _corner(*, fast: bool, ilim_high: bool = True, ron: PathCorner = "high") -> Corner:
    """An eFuse corner: fast or slow dVdt, high or low ILM overcurrent threshold (circuit breaker), and RON at the chosen end of its range."""
    span = datasheets.EFUSE_DVDT_AMPS
    return Corner(
        ron=pick(datasheets.EFUSE_RON_OHMS, ron),
        threshold=datasheets.EFUSE_THRESHOLD_RISING_VOLTS.high,
        slew_volts_per_s=slew(span.high if fast else span.low),
        ilim=pick(datasheets.EFUSE_ILIM_AMPS_AT_1K65, "high" if ilim_high else "low"),
    )


class SupplyCornerSpiceTest(unittest.TestCase):
    """Worst-corner rail level at every LED and at the Pi, from the full series path and plane mesh."""

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
