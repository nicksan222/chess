"""Tests beside registered simulation scenarios."""

import unittest
from typing import cast

from pcb.harness.base.net import Net
from pcb.harness.base.registry import BoardRegistry
from pcb.harness.base.spice.analysis import Analysis, OperatingPoint
from pcb.harness.base.spice.scenario import SpiceScenario
from pcb.harness.base.spice.source import DcVoltage, VoltageSource


class Nets(Net):
    GROUND = "GND"
    POWER = "+3V3"


class ScenarioTest(unittest.TestCase):
    def test_ground_rejects_raw_name_before_registration(self) -> None:
        board = BoardRegistry()
        with self.assertRaisesRegex(ValueError, "Net enum"):
            SpiceScenario(
                board, "normal", "power", cast(Net, "GND"), OperatingPoint(), ()
            )

    def test_duplicate_source_names_are_rejected_before_registration(self) -> None:
        board = BoardRegistry()
        source = VoltageSource("V1", Nets.POWER, Nets.GROUND, DcVoltage(3.3))
        with self.assertRaisesRegex(ValueError, "unique"):
            SpiceScenario(
                board,
                "normal",
                "nominal power",
                Nets.GROUND,
                OperatingPoint(),
                (source, source),
            )

    def test_duplicate_scenario_name_is_rejected(self) -> None:
        board = BoardRegistry()
        SpiceScenario(
            board, "normal", "nominal power", Nets.GROUND, OperatingPoint(), ()
        )
        with self.assertRaisesRegex(ValueError, "duplicate"):
            SpiceScenario(board, "normal", "second", Nets.GROUND, OperatingPoint(), ())

    def test_blank_scenario_name_does_not_register(self) -> None:
        board = BoardRegistry()
        with self.assertRaisesRegex(ValueError, "name"):
            SpiceScenario(board, " ", "power", Nets.GROUND, OperatingPoint(), ())

    def test_nonfinite_temperature_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "finite"):
            SpiceScenario(
                BoardRegistry(),
                "normal",
                "power",
                Nets.GROUND,
                OperatingPoint(),
                (),
                float("nan"),
            )

    def test_unknown_analysis_is_rejected_at_construction(self) -> None:
        with self.assertRaisesRegex(ValueError, "analysis"):
            SpiceScenario(
                BoardRegistry(),
                "normal",
                "power",
                Nets.GROUND,
                cast(Analysis, object()),
                (),
            )

    def test_scenario_name_cannot_inject_circuit_text(self) -> None:
        with self.assertRaisesRegex(ValueError, "name"):
            SpiceScenario(
                BoardRegistry(),
                "normal\nV1 a 0 100",
                "power",
                Nets.GROUND,
                OperatingPoint(),
                (),
            )
