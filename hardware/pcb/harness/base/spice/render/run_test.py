"""Tests beside handling of ngspice process output and measured results."""

import unittest

from pcb.harness import Limit
from pcb.harness.base.spice.render.run import parse_output


class RunTest(unittest.TestCase):
    def test_reads_a_valid_measured_result(self) -> None:
        output = "result_r2_0 = 1.650000e+00\nngspice done\n"
        self.assertEqual(
            parse_output(output, {"result_r2_0": Limit(1.5, 1.8)}),
            {"result_r2_0": 1.65},
        )

    def test_error_text_fails_even_when_process_exits_zero(self) -> None:
        output = "Error: no such vector\nresult_r2_0 = 1.65\n"
        with self.assertRaisesRegex(ValueError, "ngspice error"):
            parse_output(output, {"result_r2_0": Limit(1.5, 1.8)})

    def test_missing_result_fails(self) -> None:
        with self.assertRaisesRegex(ValueError, "missing result"):
            parse_output("ngspice done", {"result_r2_0": Limit(1.5, 1.8)})

    def test_out_of_window_result_fails(self) -> None:
        with self.assertRaisesRegex(ValueError, "outside"):
            parse_output("result_r2_0 = 1.2", {"result_r2_0": Limit(1.5, 1.8)})
