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
