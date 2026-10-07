"""Native pad and logical-pin regression checks for B4PS-VH."""

import unittest

import pcbnew

from pcb.components.connectors.power_connector_4_pin import (
    POWER_HEADER_DEFINITION,
    PowerConnector4Pin,
)
from pcb.harness import BoardOutline, Circuit, Net, Placement
from pcb.harness.base.pcbnew.render.board import render_board


class Nets(Net):
    A = "A"
    B = "B"


class PowerConnector4PinTest(unittest.TestCase):
    def test_shared_mating_geometry_is_adapted_to_the_pcb_definition(self) -> None:
        self.assertEqual(
            tuple(
                (zone.start_mm, zone.end_mm, zone.width_mm, zone.height_mm, zone.role)
                for zone in POWER_HEADER_DEFINITION.mated_zones
            ),
            (
                (-5.45, 16.05, 15.8, 10.5, "housing"),
                (16.05, 19.55, 15.8, 10.5, "wire_exit"),
            ),
        )

    def test_product_pin_mapping_and_native_lands(self) -> None:
        circuit = Circuit(Nets, outline=BoardOutline(160, 160))
        component = circuit.place(
            PowerConnector4Pin,
            reference="U1",
            placement=Placement(0, 0),
            purpose="component contract check",
            dc_input=Nets.A,
            ground=Nets.B,
            fused_to_switch=Nets.A,
            run=Nets.B,
        )
        self.assertEqual(component.definition.product.part_number, "B4PS-VH")
        native = render_board(circuit)
        footprint = next(iter(native.GetFootprints()))
        pads = {pad.GetNumber(): pad for pad in footprint.Pads()}
        expected = (
            ("4", 5.939999, 4.45, 2.45, 2.45, 1.65, 0, "B"),
            ("3", 1.98, 4.45, 2.45, 2.45, 1.65, 0, "A"),
            ("2", -1.98, 4.45, 2.45, 2.45, 1.65, 0, "B"),
            ("1", -5.939999, 4.45, 2.45, 2.45, 1.65, 1, "A"),
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
