"""Native pad and logical-pin regression checks for CC0603KRX7R9BB103."""

import unittest

import pcbnew

from pcb.components.capacitors.capacitor_10_nanofarad import Capacitor10Nanofarad
from pcb.harness import BoardOutline, Circuit, Net, Placement
from pcb.harness.base.pcbnew.render.board import render_board


class Nets(Net):
    A = "A"
    B = "B"


class Capacitor10NanofaradTest(unittest.TestCase):
    def test_product_pin_mapping_and_native_lands(self) -> None:
        circuit = Circuit(Nets, outline=BoardOutline(160, 160))
        component = circuit.place(
            Capacitor10Nanofarad,
            reference="C1",
            placement=Placement(0, 0),
            purpose="component contract check",
            terminal_a=Nets.A,
            terminal_b=Nets.B,
        )
        self.assertEqual(component.definition.product.part_number, "CC0603KRX7R9BB103")
        self.assertEqual(component.simulation_model().parameters[0].value, 1e-08)
        self.assertEqual(component.rated_volts, 50)
        native = render_board(circuit)
        footprint = next(iter(native.GetFootprints()))
        pads = {pad.GetNumber(): pad for pad in footprint.Pads()}
        expected = (
            ("2", 0.675, -0.0, 0.65, 0.7, 0.0, 1, "B"),
            ("1", -0.675, -0.0, 0.65, 0.7, 0.0, 1, "A"),
        )
        self.assertEqual(set(pads), {row[0] for row in expected})
        for number, x, y, width, height, drill, shape, net in expected:
            with self.subTest(pad=number):
                pad = pads[number]
                self.assertAlmostEqual(
                    pcbnew.ToMM(pad.GetPosition().x), 80 + x, places=5
                )
                self.assertAlmostEqual(
                    pcbnew.ToMM(pad.GetPosition().y), 80 - y, places=5
                )
                self.assertAlmostEqual(pcbnew.ToMM(pad.GetSize().x), width, places=5)
                self.assertAlmostEqual(pcbnew.ToMM(pad.GetSize().y), height, places=5)
                self.assertAlmostEqual(
                    pcbnew.ToMM(pad.GetDrillSize().x), drill, places=5
                )
                self.assertEqual(pad.GetShape(), shape)
                self.assertEqual(pad.GetNetname(), net)
