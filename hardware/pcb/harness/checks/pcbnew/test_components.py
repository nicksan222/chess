"""Apply the same native checks to every registered component definition."""

import tempfile
import unittest
from enum import StrEnum
from pathlib import Path
from typing import cast

import pcbnew

from pcb.components.catalog import PCB_DEFINITIONS
from pcb.harness import (
    BoardComponent,
    BoardOutline,
    Circuit,
    ComponentDefinition,
    Net,
    Placement,
)
from pcb.harness.base.geometry import Side
from pcb.harness.base.pcbnew.render.board import render_board

from .board import validate_board


class Nets(Net):
    FIRST = "FIRST"
    SECOND = "SECOND"


class NativeComponentsTest(unittest.TestCase):
    def test_every_component_has_connected_pads_inside_closed_courtyards(self) -> None:
        for entry in PCB_DEFINITIONS:
            definition = cast(ComponentDefinition[StrEnum], entry)
            for side in Side:
                for rotation in (0, 90, 180, 270):
                    with self.subTest(
                        product=definition.product.key, side=side, rotation=rotation
                    ):
                        circuit = Circuit(Nets, outline=BoardOutline(160, 160))
                        circuit.place(
                            BoardComponent,
                            reference="U1",
                            definition=definition,
                            placement=Placement(0, 0, rotation, side),
                            purpose="automatic catalog checks",
                            pins={
                                pin: (Nets.FIRST if index % 2 else Nets.SECOND)
                                for index, pin in enumerate(definition.pin_type)
                            },
                        )
                        native = render_board(circuit)
                        validate_board(circuit, native)
                        with tempfile.TemporaryDirectory() as directory:
                            path = str(Path(directory) / "component.kicad_pcb")
                            pcbnew.SaveBoard(path, native)
                            reopened = pcbnew.LoadBoard(path)
                            validate_board(circuit, reopened)
                            original = next(iter(native.GetFootprints()))
                            restored = next(iter(reopened.GetFootprints()))
                            original_pads = {
                                pad.GetNumber(): pad for pad in original.Pads()
                            }
                            for pad in restored.Pads():
                                expected = original_pads[pad.GetNumber()]
                                self.assertEqual(pad.GetShape(), expected.GetShape())
                                self.assertEqual(pad.GetSize(), expected.GetSize())
                                self.assertEqual(
                                    pad.GetPosition(), expected.GetPosition()
                                )
                                self.assertEqual(
                                    pad.GetDrillSize(), expected.GetDrillSize()
                                )
