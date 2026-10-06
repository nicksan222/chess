"""Tests beside conversion of every supported stimulus type."""

import unittest

from pcb.harness.base.net import Net
from pcb.harness.base.spice import CurrentSource, DcVoltage, PulseVoltage, VoltageSource
from pcb.harness.base.spice.render.nodes import NodeMap
from pcb.harness.base.spice.render.source import render_source


class Nets(Net):
    GROUND = "GND"
    POWER = "+3V3"


class SourceRenderTest(unittest.TestCase):
    def setUp(self) -> None:
        self.nodes = NodeMap((Nets.GROUND, Nets.POWER), Nets.GROUND)

    def test_dc_voltage_source(self) -> None:
        source = VoltageSource("VPOWER", Nets.POWER, Nets.GROUND, DcVoltage(3.3))
        # The row preserves polarity: 3.3 V from POWER to GROUND.
        self.assertEqual(render_source(source, self.nodes), "VPOWER n1 0 DC 3.3")

    def test_dc_voltage_preserves_declared_precision(self) -> None:
        """A small intentional voltage difference survives netlist conversion."""
        source = VoltageSource("V1", Nets.POWER, Nets.GROUND, DcVoltage(1.0000001))
        self.assertEqual(render_source(source, self.nodes), "V1 n1 0 DC 1.0000001")

    def test_pulse_voltage_source(self) -> None:
        pulse = PulseVoltage(0, 3.3, 0, 1e-6, 1e-6, 5e-6, 10e-6)
        source = VoltageSource("VCLOCK", Nets.POWER, Nets.GROUND, pulse)
        # Pulse timing fields keep their declared order and use seconds.
        self.assertEqual(
            render_source(source, self.nodes),
            "VCLOCK n1 0 PULSE(0 3.3 0 1e-06 1e-06 5e-06 1e-05)",
        )

    def test_constant_current_source(self) -> None:
        source = CurrentSource("ILOAD", Nets.POWER, Nets.GROUND, 0.02)
        # This row records current in amperes, directed from POWER toward GROUND.
        self.assertEqual(render_source(source, self.nodes), "ILOAD n1 0 DC 0.02")

    def test_wrong_source_designator_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "start with V"):
            render_source(
                VoltageSource("POWER", Nets.POWER, Nets.GROUND, DcVoltage(3.3)),
                self.nodes,
            )

    def test_ac_voltage_excitation_is_rendered(self) -> None:
        source = VoltageSource(
            "V1", Nets.POWER, Nets.GROUND, DcVoltage(0), ac_magnitude_volts=1
        )
        self.assertEqual(render_source(source, self.nodes), "V1 n1 0 DC 0 AC 1")

    def test_current_source_needs_i_designator(self) -> None:
        with self.assertRaisesRegex(ValueError, "start with I"):
            render_source(
                CurrentSource("LOAD", Nets.POWER, Nets.GROUND, 0.02), self.nodes
            )

    def test_ac_excitation_on_pulse_is_rejected(self) -> None:
        pulse = PulseVoltage(0, 3.3, 0, 1e-6, 1e-6, 5e-6, 10e-6)
        source = VoltageSource(
            "V1", Nets.POWER, Nets.GROUND, pulse, ac_magnitude_volts=1
        )
        with self.assertRaisesRegex(ValueError, "requires a DC waveform"):
            render_source(source, self.nodes)
