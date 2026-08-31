"""Fabrication cannot bypass connectivity or KiCad's native checks."""

import json
import unittest
from pathlib import Path

PCB = Path(__file__).resolve().parents[1]


class ReleasePolicyTest(unittest.TestCase):
    def test_every_single_pad_group_is_an_explicit_no_connect(self):
        design = json.loads((PCB / "design/netlist.json").read_text())
        for connection in design["projects"]["board"]["connections"]:
            with self.subTest(connection=connection):
                self.assertEqual(
                    connection.get("no_connect", False), len(connection["pads"]) == 1
                )

    def test_the_project_has_no_drc_exclusions(self):
        project = json.loads((PCB / "chess-board.kicad_pro").read_text())
        self.assertEqual(
            project["board"]["design_settings"].get("drc_exclusions", []), []
        )

    def test_the_runner_enforces_the_release_gate_before_gerbers(self):
        runner = (PCB.parents[1] / "tools/pcb").read_text()
        gate = runner.index("validate_release.py")
        fabrication = runner.index("pcb export gerbers")
        self.assertLess(gate, fabrication)
        self.assertIn("--severity-exclusions", runner)


if __name__ == "__main__":
    unittest.main()
