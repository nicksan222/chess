"""Tests beside conversion of typed measurements into ngspice controls."""

import unittest

from pcb.harness import Endpoint, Limit, Observation, SpiceRequirement
from pcb.harness.base.net import Net
from pcb.harness.base.spice.analysis import AcSweep, OperatingPoint, Transient
from pcb.harness.base.spice.measurement import CurrentThrough, VoltageAt, VoltageBetween
from pcb.harness.base.spice.render.measurement import render_measurement
from pcb.harness.base.spice.render.nodes import NodeMap


class Nets(Net):
    GROUND = "GND"
    POWER = "+3V3"
    OUT = "OUT"


class MeasurementRenderTest(unittest.TestCase):
    def setUp(self) -> None:
        self.nodes = NodeMap((Nets.GROUND, Nets.POWER, Nets.OUT), Nets.GROUND)
        self.nets = {Endpoint("U1", "1"): Nets.POWER, Endpoint("U1", "2"): Nets.OUT}

    def test_operating_point_pin_voltage(self) -> None:
        check = SpiceRequirement(
            "normal",
            VoltageAt(Endpoint("U1", "2")),
            Observation.SINGLE,
            Limit(0, 3.3),
            "output",
        )
        # U1 pin 2 maps to n2; node voltage is measured relative to scenario ground.
        self.assertEqual(
            render_measurement(
                "result_u1_0", check, OperatingPoint(), self.nets, self.nodes
            ),
            "let result_u1_0 = v(n2)",
        )

    def test_transient_voltage_difference_maximum(self) -> None:
        check = SpiceRequirement(
            "step",
            VoltageBetween(Endpoint("U1", "1"), Endpoint("U1", "2")),
            Observation.MAXIMUM,
            Limit(0, 3.3),
            "drop",
        )
        # MAX applies to the first-minus-second voltage across the whole transient.
        self.assertEqual(
            render_measurement(
                "result_u1_0", check, Transient(0.01, 0.0001), self.nets, self.nodes
            ),
            "meas tran result_u1_0 MAX v(n1,n2)",
        )

    def test_operating_point_source_current(self) -> None:
        check = SpiceRequirement(
            "normal", CurrentThrough("VPOWER"), Observation.SINGLE, Limit(-1, 1), "load"
        )
        # The current expression names the source and retains ngspice's sign convention.
        self.assertEqual(
            render_measurement(
                "result_u1_0", check, OperatingPoint(), self.nets, self.nodes
            ),
            "let result_u1_0 = i(VPOWER)",
        )

    def test_incompatible_observation_is_rejected(self) -> None:
        check = SpiceRequirement(
            "normal",
            VoltageAt(Endpoint("U1", "2")),
            Observation.MAXIMUM,
            Limit(0, 3.3),
            "output",
        )
        with self.assertRaisesRegex(ValueError, "operating point"):
            render_measurement(
                "result_u1_0", check, OperatingPoint(), self.nets, self.nodes
            )

    def test_transient_final_uses_duration(self) -> None:
        check = SpiceRequirement(
            "step",
            VoltageAt(Endpoint("U1", "2")),
            Observation.FINAL,
            Limit(0, 3.3),
            "output",
        )
        self.assertEqual(
            render_measurement(
                "result_u1_0", check, Transient(0.01, 0.0001), self.nets, self.nodes
            ),
            "meas tran result_u1_0 FIND v(n2) AT=0.01",
        )

    def test_ac_magnitude_is_named_before_measurement(self) -> None:
        check = SpiceRequirement(
            "response",
            VoltageAt(Endpoint("U1", "2")),
            Observation.MAXIMUM,
            Limit(0, 1),
            "gain",
        )
        self.assertEqual(
            render_measurement(
                "result_u1_0", check, AcSweep(10, 10000, 20), self.nets, self.nodes
            ),
            "let magnitude_result_u1_0 = mag(v(n2))\n"
            "meas ac result_u1_0 MAX magnitude_result_u1_0",
        )

    def test_unsafe_result_name_is_rejected(self) -> None:
        check = SpiceRequirement(
            "normal",
            VoltageAt(Endpoint("U1", "2")),
            Observation.SINGLE,
            Limit(0, 3.3),
            "output",
        )
        with self.assertRaisesRegex(ValueError, "safe"):
            render_measurement(
                "result_u1;quit", check, OperatingPoint(), self.nets, self.nodes
            )

    def test_missing_measured_endpoint_is_rejected(self) -> None:
        check = SpiceRequirement(
            "normal",
            VoltageAt(Endpoint("U9", "1")),
            Observation.SINGLE,
            Limit(0, 3.3),
            "output",
        )
        with self.assertRaisesRegex(ValueError, "unknown endpoint"):
            render_measurement(
                "result_u1_0", check, OperatingPoint(), self.nets, self.nodes
            )
