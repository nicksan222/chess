"""Local clearance rules are scoped to the actual placed package, on its own face."""

import json
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path
from typing import cast

from pcb.harness import (
    BoardComponent,
    Circuit,
    PackageClearance,
    PackageRouting,
    Placement,
    Side,
)
from pcb.harness.base.pcbnew.render.board_test import Nets, Pin, sample_board

from .design_rules import DesignRules, write_rules
from .routing.settings import RoutingSettings


class DesignRulesTest(unittest.TestCase):
    def test_local_exception_uses_instance_reference_and_bottom_face(self) -> None:
        sample = sample_board()
        part = cast(BoardComponent[Pin], sample.components()[0])
        circuit = Circuit(Nets, outline=sample.outline)
        circuit.place(
            BoardComponent,
            reference="Protection",
            definition=replace(
                part.definition,
                routing=PackageRouting(clearance=PackageClearance(0.16, 0.2, 0.6)),
            ),
            placement=Placement(0, 0, side=Side.BOTTOM),
            purpose="scoped package rule",
            pins={Pin.A: Nets.POWER, Pin.B: Nets.GROUND},
        )
        with tempfile.TemporaryDirectory() as directory:
            destination = Path(directory)
            project = destination / "test.kicad_pro"
            project.write_text(
                json.dumps(
                    {
                        "board": {"design_settings": {"rules": {}}},
                        "net_settings": {"classes": [{}]},
                    }
                )
            )
            write_rules(circuit, DesignRules(RoutingSettings()), destination, "test")
            text = (destination / "test.kicad_dru").read_text()
            self.assertIn("memberOfFootprint('Protection')", text)
            self.assertIn("intersectsCourtyard('Protection')", text)
            self.assertIn('(layer "B.Cu")', text)
            self.assertNotIn("U74", text)
            self.assertNotIn('(layer "F.Cu")', text)
            self.assertEqual(
                DesignRules(RoutingSettings()).minimums(circuit), (0.16, 0.2)
            )

    def test_routing_cannot_relax_the_declared_process_floor(self) -> None:
        with self.assertRaisesRegex(ValueError, "process floors"):
            DesignRules(RoutingSettings(clearance_mm=0.1))
