"""Native pad and logical-pin regression checks for SM04B-SRSS-TB."""

import unittest

import pcbnew

from pcb.components.connectors.oled_connector_4_pin import (
    OLED_HEADER_DEFINITION,
    OledConnector4Pin,
)
from pcb.harness import BoardOutline, Circuit, Net, Placement
from pcb.harness.base.pcbnew.render.board import render_board


class Nets(Net):
    A = "A"
    B = "B"


class OledConnector4PinTest(unittest.TestCase):
    def test_shared_mating_geometry_is_adapted_to_the_pcb_definition(self) -> None:
        self.assertEqual(
            tuple(
                (zone.start_mm, zone.end_mm, zone.width_mm, zone.height_mm, zone.role)
                for zone in OLED_HEADER_DEFINITION.mated_zones
            ),
            (
                (3.24, 5.25, 6.0, 2.95, "housing"),
                (5.25, 7.25, 6.0, 1.95, "wire_exit"),
            ),
        )

    def test_product_pin_mapping_and_native_lands(self) -> None:
        circuit = Circuit(Nets, outline=BoardOutline(160, 160))
        component = circuit.place(
            OledConnector4Pin,
            reference="U1",
            placement=Placement(0, 0),
            purpose="component contract check",
            ground=Nets.A,
            three_volts_three=Nets.B,
            i2c_clock=Nets.A,
            i2c_data=Nets.B,
            mounting_tab_a=Nets.A,
            mounting_tab_b=Nets.B,
        )
        self.assertEqual(component.definition.product.part_number, "SM04B-SRSS-TB")
        native = render_board(circuit)
        footprint = next(iter(native.GetFootprints()))
        pads = {pad.GetNumber(): pad for pad in footprint.Pads()}
        expected = (
            ("6", 2.8, -1.9375, 1.2, 1.8, 0.0, 2, "B"),
            ("5", -2.8, -1.9375, 1.2, 1.8, 0.0, 2, "A"),
            ("4", 1.5, 1.9375, 0.6, 1.55, 0.0, 2, "B"),
            ("3", 0.5, 1.9375, 0.6, 1.55, 0.0, 2, "A"),
            ("2", -0.5, 1.9375, 0.6, 1.55, 0.0, 2, "B"),
            ("1", -1.5, 1.9375, 0.6, 1.55, 0.0, 1, "A"),
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
