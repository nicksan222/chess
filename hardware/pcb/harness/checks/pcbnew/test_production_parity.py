"""Transitional native parity with the board pipeline being replaced."""

import unittest
from enum import StrEnum
from typing import cast

import pcbnew

from pcb.components.catalog import PCB_DEFINITIONS
from pcb.definition.parts.catalog import PCB_PARTS
from pcb.harness import (
    BoardComponent,
    BoardOutline,
    Circuit,
    ComponentDefinition,
    Net,
    Placement,
)
from pcb.harness.base.pcbnew.render.board import render_board


class Nets(Net):
    CONNECTED = "CONNECTED"


class ProductionParityTest(unittest.TestCase):
    def test_native_copper_and_process_settings_match_production(self) -> None:
        for entry in PCB_DEFINITIONS:
            definition = cast(ComponentDefinition[StrEnum], entry)
            with self.subTest(product=definition.product.key):
                circuit = Circuit(Nets, outline=BoardOutline(160, 160))
                circuit.place(
                    BoardComponent,
                    reference="U1",
                    definition=definition,
                    placement=Placement(0, 0),
                    purpose="contract parity",
                    pins={pin: Nets.CONNECTED for pin in definition.pin_type},
                )
                board = render_board(circuit)
                footprint = next(iter(board.GetFootprints()))
                native = {pad.GetNumber(): pad for pad in footprint.Pads()}
                original = PCB_PARTS[definition.product.key].template
                for expected in original.Pads():
                    pad = native[expected.GetNumber()]
                    self.assertEqual(pad.GetShape(), expected.GetShape())
                    self.assertEqual(pad.GetAttribute(), expected.GetAttribute())
                    self.assertEqual(pad.GetSize(), expected.GetSize())
                    self.assertEqual(pad.GetDrillSize(), expected.GetDrillSize())
                    self.assertEqual(
                        pad.GetLocalSolderMaskMargin(),
                        expected.GetLocalSolderMaskMargin(),
                    )
                    self.assertEqual(
                        pad.GetLocalThermalSpokeWidthOverride(),
                        expected.GetLocalThermalSpokeWidthOverride(),
                    )

                    # Compare actual custom and standard copper, including the eFuse's legs.
                    def copper_area(item: pcbnew.PAD) -> float:
                        polygon = pcbnew.SHAPE_POLY_SET()
                        item.TransformShapeToPolygon(
                            polygon, pcbnew.F_Cu, 0, 1000, pcbnew.ERROR_INSIDE
                        )
                        return polygon.Area()

                    self.assertAlmostEqual(
                        copper_area(pad) / 1e12, copper_area(expected) / 1e12, places=5
                    )
