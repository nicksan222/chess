"""LED rail switch at power-up and enable (S6, user decision D1) [BEH].

The U74 front end (efuse_model) feeds +5V with its bulk capacitors and the Pi/logic
load; Q1/Q2 come from led_switch_model. Cases:
- power-up with LED_EN held low by R14 and the chain modelled as powering up lit:
  LED_5V stays off and the eFuse never sees more than ILIM;
- enable with a blanked chain: the LED_5V ramp keeps the input under ILIM and
  barely dips +5V;
- enable into a lit chain: the residual (ASSUMPTION "LED power-up state") is
  recorded, not passed, at both of U74's overcurrent branches;
- overload (S6d): full white from a running board and a lit chain at enable trip
  U74 (fast trip into limiting, or the ITIMER breaker) with F1's I2t inside the
  20 % pulse rule;
- U5's LED outputs (S6b H6): through enable and disable, at every corner, U6's
  DI/CI never sit more than 0.3 V above LED_5V (SK9822-A Rev 01 §8 VIN
  -0.3..VDD+0.3 V), so U6's input clamps never back-power the chain, and while U5
  is Hi-Z the pull-downs hold them within 0.3 V of ground (S6d).
"""

from __future__ import annotations

import itertools
import unittest

from shared.electronics import sk9822
from spice import datasheets
from spice.circuit import SpiceCircuit
from spice.efuse_model import Corner, EfuseBoard, TimerCorner, slew
from spice.led_switch_model import (
    Q1_THRESHOLD_CORNERS,
    Q2_THRESHOLD_CORNERS,
    buffer_rows,
    switch_rows,
    u75_output,
)
from spice.plane_mesh import routed_board
from spice.power_path import FUSES, pick, series_path
from spice.residuals import residual
from spice.support import board_circuits, run_circuit

ENABLE_AT_MS = 60.0


def _corner(*, ilim_high: bool) -> Corner:
    """An eFuse corner with the earliest threshold and the fastest slew; only the ILM overcurrent threshold (circuit breaker) varies (`ilim_high`)."""
    return Corner(
        ron=datasheets.EFUSE_RON_OHMS.low,
        threshold=datasheets.EFUSE_THRESHOLD_RISING_VOLTS.high,
        slew_volts_per_s=slew(datasheets.EFUSE_DVDT_AMPS.high),
        ilim=pick(datasheets.EFUSE_ILIM_AMPS_AT_1K65, "high" if ilim_high else "low"),
    )


class LedSwitchSpiceTest(unittest.TestCase):
    """LED rail switch behaviour: stays off until enabled, enable ramp, lit-chain residual and output-enable timing."""

    stage: EfuseBoard
    path_ohms: float

    @classmethod
    def setUpClass(cls) -> None:
        """Build the eFuse front end and the series-path resistance once."""
        cls.stage = EfuseBoard(board_circuits())
        fuse = cls.stage.board.components["F1"].GetValue()
        cls.path_ohms = series_path(routed_board(), fuse, "low").total_ohms

    def _bulk(self) -> list[str]:
        """SPICE rows for every capacitor fitted between +5V and GND (the bulk and bypass capacitance the eFuse charges)."""
        rows: list[str] = []
        board = self.stage.board
        for reference, component in board.components.items():
            nets = {board.net_by_endpoint.get((reference, pin)) for pin in ("1", "2")}
            if component.GetFieldText("PartKey").startswith("CAP_") and nets == {
                "+5V",
                "GND",
            }:
                key = component.GetFieldText("PartKey")
                value = {"CAP_560U": "560u", "CAP_10U": "10u", "CAP_100N": "100n"}[key]
                rows.append(f"C{reference} out 0 {value}")
        return rows

    def _circuit(
        self,
        name: str,
        *,
        lit: bool,
        enable: bool,
        ilim_high: bool,
        q1_vto: float = Q1_THRESHOLD_CORNERS[0],
        full_white_ms: float | None = None,
        timer: TimerCorner = "slow",
    ) -> SpiceCircuit:
        """The power-up/enable circuit: `lit` models a chain that powers up lit, `enable` raises LED_EN, `ilim_high` and `q1_vto` pick corners.

        `full_white_ms` steps the chain to full white at that time (S6d); `timer`
        picks U74's ITIMER blanking corner.
        """
        supply = datasheets.PSU_VOLTS.high
        circuit = self.stage.front_end(
            f"Generated chess-board LED switch, {name} [BEH]",
            _corner(ilim_high=ilim_high),
            f"PULSE(0 {supply} 0 1u 1u 1 2)",
            path_ohms=self.path_ohms,
            run_on=True,
            timer=timer,
        )
        circuit.rows.extend(self._bulk())
        circuit.rows.append(
            f"RHOST out 0 {datasheets.PSU_RATED_VOLTS / datasheets.HOST_AND_LOGIC_AMPS}"
        )
        circuit.rows.extend(
            switch_rows(
                self.stage.board,
                lit=lit,
                rds_ohms=datasheets.LED_SWITCH_OHMS.high,
                q1_vto=q1_vto,
            )
        )
        drive = (
            f"PWL(0 0 {ENABLE_AT_MS}m 0 {ENABLE_AT_MS + 0.001}m 3.3)" if enable else "0"
        )
        circuit.rows.append(f"VEN en_pi 0 {drive}")
        end_ms = ENABLE_AT_MS + 20
        if full_white_ms is not None:
            # The chain's channels on at 18 mA once VDD clears the LEDs' 3 V.
            channels = LED_COUNT * 3 * datasheets.SK9822_CHANNEL_AMPS_MAX
            circuit.rows.extend(
                (
                    f"VWHITE white 0 PWL(0 0 {full_white_ms}m 0 {full_white_ms + 0.01}m 1)",
                    (
                        f"BWHITE led 0 I={{V(white) * {channels}"
                        " * 0.5 * (1 + tanh((V(led) - 3.0) / 0.1))}"
                    ),
                )
            )
            end_ms = full_white_ms + OVERLOAD_WINDOW_MS + 1
        circuit.rows.append(f".tran 10u {end_ms}m 0 10u uic")
        return circuit

    def test_lit_chain_stays_off_until_enabled(self) -> None:
        # Worst case for a trip: the lowest ILIM, a chain that would light at once,
        # U74's fastest dV/dt and Q1's lowest |VGS(th)| (reviewer-s6 m1), where
        # C145/CGD coupling the +5V ramp onto Q1's gate comes closest to turning
        # it on.
        circuit = self._circuit(
            "off, lit chain", lit=True, enable=False, ilim_high=False
        )
        circuit.controls.extend(
            (
                "meas tran result_led_rail_max MAX v(led)",
                "meas tran result_input_max MAX i(vpsu) FROM=5m",
                "let result_input_amps = -result_input_max",
                "meas tran result_input_min MIN i(vpsu) FROM=5m",
                "let result_input_peak = -result_input_min",
                "meas tran result_rail_end FIND v(out) AT=79m",
            )
        )
        circuit.expect("led_rail_max", -0.01, 0.5)
        circuit.expect("input_peak", 0.0, datasheets.EFUSE_ILIM_AMPS_AT_1K65.low)
        circuit.expect("rail_end", 4.9, datasheets.PSU_VOLTS.high)
        run_circuit("test_led_switch_off_lit.py", circuit)

    def test_enable_ramp_stays_under_the_current_limit(self) -> None:
        circuit = self._circuit(
            "enable, blanked", lit=False, enable=True, ilim_high=False
        )
        start = f"{ENABLE_AT_MS}m"
        circuit.controls.extend(
            (
                f"meas tran result_input_min MIN i(vpsu) FROM={start}",
                "let result_input_peak = -result_input_min",
                f"meas tran result_rail_min MIN v(out) FROM={start}",
                f"meas tran t10 WHEN v(led)=0.5 RISE=1 FROM={start}",
                f"meas tran t90 WHEN v(led)=4.5 RISE=1 FROM={start}",
                "let result_ramp_ms = (t90 - t10) * 1000",
                "print result_ramp_ms",
                f"meas tran result_led_end FIND v(led) AT={ENABLE_AT_MS + 19}m",
            )
        )
        circuit.expect("input_peak", 0.0, LED_ENABLE_INPUT_AMPS_MAX)
        circuit.expect("rail_min", datasheets.PSU_VOLTS.high - 0.05, 5.3)
        circuit.expect("ramp_ms", 0.3, 5.0)
        circuit.expect("led_end", 4.9, datasheets.PSU_VOLTS.high)
        run_circuit("test_led_switch_enable.py", circuit)
