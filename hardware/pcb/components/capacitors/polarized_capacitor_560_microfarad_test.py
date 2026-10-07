"""Native pad and logical-pin regression checks for 10ZLJ560M8X11.5."""

import unittest

import pcbnew

from pcb.components.capacitors.polarized_capacitor_560_microfarad import (
    PolarizedCapacitor560Microfarad,
)
from pcb.harness import BoardOutline, Circuit, Net, Placement
from pcb.harness.base.pcbnew.render.board import render_board


class Nets(Net):
    A = "A"
    B = "B"


class PolarizedCapacitor560MicrofaradTest(unittest.TestCase):
    def test_product_pin_mapping_and_native_lands(self) -> None:
        circuit = Circuit(Nets, outline=BoardOutline(160, 160))
        component = circuit.place(
            PolarizedCapacitor560Microfarad,
            reference="C1",
            placement=Placement(0, 0),
            purpose="component contract check",
            positive=Nets.A,
            negative=Nets.B,
        )
        self.assertEqual(component.definition.product.part_number, "10ZLJ560M8X11.5")
        native = render_board(circuit)
        footprint = next(iter(native.GetFootprints()))
        pads = {pad.GetNumber(): pad for pad in footprint.Pads()}
        expected = (
            ("2", 1.75, -0.0, 1.7, 1.7, 0.9, 0, "B"),
            ("1", -1.75, -0.0, 1.7, 1.7, 0.9, 1, "A"),
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
