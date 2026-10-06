"""Tests beside analysis setup declarations."""

import unittest

from pcb.harness.base.spice.analysis import AcSweep, Transient


class AnalysisTest(unittest.TestCase):
    def test_transient_step_must_fit_inside_duration(self) -> None:
        with self.assertRaisesRegex(ValueError, "positive and ordered"):
            Transient(0.001, 0.002)

    def test_ac_sweep_requires_increasing_frequency(self) -> None:
        with self.assertRaisesRegex(ValueError, "increasing"):
            AcSweep(1000.0, 100.0, 10)

    def test_transient_rejects_zero_step(self) -> None:
        with self.assertRaisesRegex(ValueError, "positive"):
            Transient(0.001, 0.0)

    def test_ac_sweep_rejects_zero_resolution(self) -> None:
        with self.assertRaisesRegex(ValueError, "resolution"):
            AcSweep(10.0, 100.0, 0)

    def test_ac_sweep_rejects_fractional_or_boolean_point_counts(self) -> None:
        """ngspice's points-per-decade parameter must be a real integer count."""
        for count in (1.5, True):
            with (
                self.subTest(count=count),
                self.assertRaisesRegex(ValueError, "integer"),
            ):
                AcSweep(10.0, 100.0, count)  # type: ignore[arg-type]
