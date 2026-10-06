"""Tests beside conversion of supported component models to circuit elements."""

import unittest
from enum import StrEnum

from pcb.harness.base.net import Net
from pcb.harness.base.spice import ModelParameter, SpiceModel
from pcb.harness.base.spice.render.model import render_model
from pcb.harness.base.spice.render.nodes import NodeMap


class Nets(Net):
    GROUND = "GND"
    POWER = "+3V3"
    A = "A"


class Pin(StrEnum):
    A = "1"
    B = "2"


class ModelRenderTest(unittest.TestCase):
    def test_resistor_becomes_a_two_node_spice_element(self) -> None:
        model = SpiceModel(
            "resistor", (Pin.A, Pin.B), (ModelParameter("resistance", 1000, "ohm"),)
        )
        nodes = NodeMap((Nets.POWER, Nets.GROUND), Nets.GROUND)
        # The line preserves ordered terminals, safe node mapping and resistance.
        self.assertEqual(
            render_model("R1", model, (Nets.POWER, Nets.GROUND), nodes), "R1 n1 0 1000"
        )

    def test_resistor_preserves_precise_declared_value(self) -> None:
        """Model conversion must not silently change a component parameter."""
        model = SpiceModel(
            "resistor",
            (Pin.A, Pin.B),
            (ModelParameter("resistance", 1.0000001, "ohm"),),
        )
        nodes = NodeMap((Nets.POWER, Nets.GROUND), Nets.GROUND)
        self.assertEqual(
            render_model("R1", model, (Nets.POWER, Nets.GROUND), nodes),
            "R1 n1 0 1.0000001",
        )

    def test_unknown_model_key_fails_instead_of_omitting_a_part(self) -> None:
        nodes = NodeMap((Nets.A, Nets.GROUND), Nets.GROUND)
        with self.assertRaisesRegex(ValueError, "unsupported model"):
            render_model("U1", SpiceModel("mystery", (Pin.A,)), (Nets.A,), nodes)

    def test_resistor_rejects_wrong_parameter_unit(self) -> None:
        model = SpiceModel(
            "resistor", (Pin.A, Pin.B), (ModelParameter("resistance", 1000, "volt"),)
        )
        with self.assertRaisesRegex(ValueError, "ohm"):
            render_model(
                "R1",
                model,
                (Nets.A, Nets.GROUND),
                NodeMap((Nets.A, Nets.GROUND), Nets.GROUND),
            )

    def test_model_rejects_missing_terminal_net(self) -> None:
        model = SpiceModel(
            "resistor", (Pin.A, Pin.B), (ModelParameter("resistance", 1000, "ohm"),)
        )
        with self.assertRaisesRegex(ValueError, "terminal/net count"):
            render_model(
                "R1", model, (Nets.A,), NodeMap((Nets.A, Nets.GROUND), Nets.GROUND)
            )

    def test_resistor_rejects_zero_resistance(self) -> None:
        model = SpiceModel(
            "resistor", (Pin.A, Pin.B), (ModelParameter("resistance", 0, "ohm"),)
        )
        with self.assertRaisesRegex(ValueError, "positive resistance"):
            render_model(
                "R1",
                model,
                (Nets.A, Nets.GROUND),
                NodeMap((Nets.A, Nets.GROUND), Nets.GROUND),
            )

    def test_capacitor_becomes_a_two_node_spice_element(self) -> None:
        model = SpiceModel(
            "capacitor",
            (Pin.A, Pin.B),
            (ModelParameter("capacitance", 1e-7, "farad"),),
        )
        # A 100 nF capacitor connects the named net to the declared ground node.
        self.assertEqual(
            render_model(
                "C1",
                model,
                (Nets.A, Nets.GROUND),
                NodeMap((Nets.A, Nets.GROUND), Nets.GROUND),
            ),
            "C1 n1 0 1e-07",
        )

    def test_diode_includes_model_card_and_anode_cathode_order(self) -> None:
        model = SpiceModel(
            "diode",
            (Pin.A, Pin.B),
            (
                ModelParameter("saturation_current", 1e-12, "ampere"),
                ModelParameter("ideality_factor", 1.5, "ratio"),
                ModelParameter("series_resistance", 0.1, "ohm"),
            ),
        )
        # This is the closed-contact approximation; it does not model button motion.
        # Terminal order is anode then cathode; the model card carries diode parameters.
        self.assertEqual(
            render_model(
                "D1",
                model,
                (Nets.A, Nets.GROUND),
                NodeMap((Nets.A, Nets.GROUND), Nets.GROUND),
            ),
            "D1 n1 0 D_D1\n.model D_D1 D(Is=1e-12 N=1.5 Rs=0.1)",
        )

    def test_static_button_becomes_contact_resistance(self) -> None:
        model = SpiceModel(
            "button_static",
            (Pin.A, Pin.B),
            (ModelParameter("contact_resistance", 0.05, "ohm"),),
        )
        self.assertEqual(
            render_model(
                "SW1",
                model,
                (Nets.A, Nets.GROUND),
                NodeMap((Nets.A, Nets.GROUND), Nets.GROUND),
            ),
            "Rcontact_SW1 n1 0 0.05",
        )

    def test_diode_rejects_nonpositive_saturation_current(self) -> None:
        model = SpiceModel(
            "diode",
            (Pin.A, Pin.B),
            (
                ModelParameter("saturation_current", 0, "ampere"),
                ModelParameter("ideality_factor", 1.5, "ratio"),
                ModelParameter("series_resistance", 0.1, "ohm"),
            ),
        )
        with self.assertRaisesRegex(ValueError, "saturation_current"):
            render_model(
                "D1",
                model,
                (Nets.A, Nets.GROUND),
                NodeMap((Nets.A, Nets.GROUND), Nets.GROUND),
            )

    def test_capacitor_rejects_zero_capacitance(self) -> None:
        model = SpiceModel(
            "capacitor", (Pin.A, Pin.B), (ModelParameter("capacitance", 0, "farad"),)
        )
        with self.assertRaisesRegex(ValueError, "positive capacitance"):
            render_model(
                "C1",
                model,
                (Nets.A, Nets.GROUND),
                NodeMap((Nets.A, Nets.GROUND), Nets.GROUND),
            )

    def test_capacitor_rejects_wrong_unit(self) -> None:
        model = SpiceModel(
            "capacitor", (Pin.A, Pin.B), (ModelParameter("capacitance", 1, "ohm"),)
        )
        with self.assertRaisesRegex(ValueError, "farad"):
            render_model(
                "C1",
                model,
                (Nets.A, Nets.GROUND),
                NodeMap((Nets.A, Nets.GROUND), Nets.GROUND),
            )

    def test_diode_rejects_negative_series_resistance(self) -> None:
        model = SpiceModel(
            "diode",
            (Pin.A, Pin.B),
            (
                ModelParameter("saturation_current", 1e-12, "ampere"),
                ModelParameter("ideality_factor", 1.5, "ratio"),
                ModelParameter("series_resistance", -1, "ohm"),
            ),
        )
        with self.assertRaisesRegex(ValueError, "nonnegative series_resistance"):
            render_model(
                "D1",
                model,
                (Nets.A, Nets.GROUND),
                NodeMap((Nets.A, Nets.GROUND), Nets.GROUND),
            )

    def test_button_rejects_zero_contact_resistance(self) -> None:
        model = SpiceModel(
            "button_static",
            (Pin.A, Pin.B),
            (ModelParameter("contact_resistance", 0, "ohm"),),
        )
        with self.assertRaisesRegex(ValueError, "positive contact_resistance"):
            render_model(
                "SW1",
                model,
                (Nets.A, Nets.GROUND),
                NodeMap((Nets.A, Nets.GROUND), Nets.GROUND),
            )

    def test_each_kind_rejects_wrong_reference_prefix(self) -> None:
        models = (
            SpiceModel(
                "resistor", (Pin.A, Pin.B), (ModelParameter("resistance", 1, "ohm"),)
            ),
            SpiceModel(
                "capacitor",
                (Pin.A, Pin.B),
                (ModelParameter("capacitance", 1, "farad"),),
            ),
            SpiceModel(
                "button_static",
                (Pin.A, Pin.B),
                (ModelParameter("contact_resistance", 1, "ohm"),),
            ),
        )
        nodes = NodeMap((Nets.A, Nets.GROUND), Nets.GROUND)
        for model in models:
            with (
                self.subTest(model=model.key),
                self.assertRaisesRegex(ValueError, "reference"),
            ):
                render_model("X1", model, (Nets.A, Nets.GROUND), nodes)
