"""Native pad and logical-pin regression checks for SMBJ12CA."""

import unittest

import pcbnew

from pcb.components.tvs_diodes.bidirectional_tvs_12_volt import (
    BidirectionalTvs12Volt,
)
from pcb.harness import BoardOutline, Circuit, Net, Placement
from pcb.harness.base.pcbnew.render.board import render_board


class Nets(Net):
    A = "A"
    B = "B"


class BidirectionalTvs12VoltTest(unittest.TestCase):
    def test_product_pin_mapping_and_native_lands(self) -> None:
        circuit = Circuit(Nets, outline=BoardOutline(160, 160))
        component = circuit.place(
            BidirectionalTvs12Volt,
            reference="U1",
            placement=Placement(0, 0),
            purpose="component contract check",
            protected_input=Nets.A,
            ground=Nets.B,
        )
        self.assertEqual(component.definition.product.part_number, "SMBJ12CA")
        native = render_board(circuit)
        footprint = next(iter(native.GetFootprints()))
        pads = {pad.GetNumber(): pad for pad in footprint.Pads()}
        expected = (
            ("2", 2.23, -0.0, 2.16, 2.26, 0.0, 1, "B"),
            ("1", -2.23, -0.0, 2.16, 2.26, 0.0, 1, "A"),
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
