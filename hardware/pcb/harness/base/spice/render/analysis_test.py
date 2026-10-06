"""Tests beside conversion of the three supported analyses."""

import unittest

from pcb.harness.base.spice import AcSweep, OperatingPoint, Transient
from pcb.harness.base.spice.render.analysis import render_analysis


class AnalysisRenderTest(unittest.TestCase):
    def test_operating_point(self) -> None:
        # An operating-point request becomes ngspice's direct-current solve directive.
        self.assertEqual(render_analysis(OperatingPoint()), ".op")

    def test_transient(self) -> None:
        # The directive orders maximum step before total duration, both in seconds.
        self.assertEqual(
            render_analysis(Transient(0.001, 0.00001)), ".tran 1e-05 0.001"
        )

    def test_ac_sweep(self) -> None:
        # This checks a logarithmic sweep with the requested range and density.
        self.assertEqual(render_analysis(AcSweep(10, 10000, 20)), ".ac dec 20 10 10000")

    def test_unknown_analysis_fails(self) -> None:
        with self.assertRaisesRegex(ValueError, "unsupported"):
            render_analysis(object())  # type: ignore[arg-type]
