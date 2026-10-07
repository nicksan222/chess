"""Native pad and logical-pin regression checks for RC0603FR-07100KL."""

import unittest

import pcbnew

from pcb.components.resistors.resistor_100_kilohm import Resistor100Kilohm
from pcb.harness import BoardOutline, Circuit, Net, Placement
from pcb.harness.base.pcbnew.render.board import render_board


class Nets(Net):
    A = "A"
    B = "B"


class Resistor100KilohmTest(unittest.TestCase):
    def test_product_pin_mapping_and_native_lands(self) -> None:
        circuit = Circuit(Nets, outline=BoardOutline(160, 160))
        component = circuit.place(
            Resistor100Kilohm,
            reference="R1",
            placement=Placement(0, 0),
            purpose="component contract check",
            terminal_a=Nets.A,
            terminal_b=Nets.B,
        )
        self.assertEqual(component.definition.product.part_number, "RC0603FR-07100KL")
        self.assertEqual(component.simulation_model().parameters[0].value, 100000)
        self.assertEqual(component.tolerance_percent, 1)
        native = render_board(circuit)
        footprint = next(iter(native.GetFootprints()))
        pads = {pad.GetNumber(): pad for pad in footprint.Pads()}
        expected = (
            ("2", 0.85, -0.0, 0.9, 0.8, 0.0, 1, "B"),
            ("1", -0.85, -0.0, 0.9, 0.8, 0.0, 1, "A"),
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
