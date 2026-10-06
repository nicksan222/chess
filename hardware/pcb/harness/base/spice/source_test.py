"""Tests beside electrical source and waveform declarations."""

import unittest
from typing import cast

from pcb.harness.base.net import Net
from pcb.harness.base.spice.source import (
    CurrentSource,
    DcVoltage,
    PulseVoltage,
    VoltageSource,
)


class Nets(Net):
    GROUND = "GND"
    POWER = "+3V3"


class SourceTest(unittest.TestCase):
    def test_voltage_source_rejects_raw_net_name(self) -> None:
        with self.assertRaisesRegex(ValueError, "Net enum"):
            VoltageSource("V1", cast(Net, "+3V3"), cast(Net, "GND"), DcVoltage(3.3))

    def test_pulse_must_fit_in_one_period(self) -> None:
        with self.assertRaisesRegex(ValueError, "exceed"):
            PulseVoltage(0, 3.3, 0, 0.2, 0.2, 0.8, 1.0)

    def test_voltage_source_needs_two_different_nets(self) -> None:
        with self.assertRaisesRegex(ValueError, "different nets"):
            VoltageSource("V1", Nets.POWER, Nets.POWER, DcVoltage(3.3))

    def test_current_source_needs_finite_current(self) -> None:
        with self.assertRaisesRegex(ValueError, "finite current"):
            CurrentSource("I1", Nets.POWER, Nets.GROUND, float("nan"))

    def test_dc_source_rejects_nan_voltage(self) -> None:
        with self.assertRaisesRegex(ValueError, "finite"):
            DcVoltage(float("nan"))

    def test_pulse_rejects_negative_delay(self) -> None:
        with self.assertRaisesRegex(ValueError, "negative"):
            PulseVoltage(0, 3.3, -0.1, 0.1, 0.1, 0.3, 1.0)

    def test_source_rejects_blank_name(self) -> None:
        with self.assertRaisesRegex(ValueError, "name"):
            VoltageSource(" ", Nets.POWER, Nets.GROUND, DcVoltage(3.3))

    def test_ac_excitation_must_have_positive_magnitude(self) -> None:
        with self.assertRaisesRegex(ValueError, "AC magnitude"):
            VoltageSource(
                "V1", Nets.POWER, Nets.GROUND, DcVoltage(0), ac_magnitude_volts=0
            )
