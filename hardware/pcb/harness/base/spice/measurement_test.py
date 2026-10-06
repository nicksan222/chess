"""Tests beside typed simulation measurements and pass bands."""

import unittest
from typing import cast

from pcb.harness.base.connections import Endpoint
from pcb.harness.base.spice.measurement import (
    CurrentThrough,
    Limit,
    Measurement,
    Observation,
    SpiceRequirement,
    VoltageAt,
    VoltageBetween,
)


class MeasurementTest(unittest.TestCase):
    def test_voltage_difference_requires_distinct_points(self) -> None:
        pin = Endpoint("U1", "1")
        with self.assertRaisesRegex(ValueError, "distinct"):
            VoltageBetween(pin, pin)

    def test_limit_bounds_must_be_ordered(self) -> None:
        with self.assertRaisesRegex(ValueError, "ordered"):
            Limit(3.5, 3.1)

    def test_requirement_needs_a_reason(self) -> None:
        with self.assertRaisesRegex(ValueError, "rationale"):
            SpiceRequirement(
                "normal",
                VoltageAt(Endpoint("U1", "1")),
                Observation.SINGLE,
                Limit(3.1, 3.5),
                "",
            )

    def test_limit_rejects_nan(self) -> None:
        with self.assertRaisesRegex(ValueError, "finite"):
            Limit(float("nan"), 3.5)

    def test_current_measurement_needs_source(self) -> None:
        with self.assertRaisesRegex(ValueError, "source name"):
            CurrentThrough(" ")

    def test_unknown_measurement_is_rejected_at_construction(self) -> None:
        with self.assertRaisesRegex(ValueError, "measurement"):
            SpiceRequirement(
                "normal",
                cast(Measurement, object()),
                Observation.SINGLE,
                Limit(0, 1),
                "claim",
            )
