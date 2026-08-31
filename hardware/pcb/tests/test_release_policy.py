"""Fabrication cannot bypass connectivity or KiCad's native checks."""

import json
import unittest
from pathlib import Path

import audit as board_audit
import footprints
from shared.components import COMPONENTS
from write_schematic import render as render_schematic
from write_schematic import render_symbol_library

PCB = Path(__file__).resolve().parents[1]


class ReleasePolicyTest(unittest.TestCase):
    def test_every_single_pad_group_is_an_explicit_no_connect(self):
        design = json.loads((PCB / "design/netlist.json").read_text())
        for connection in design["projects"]["board"]["connections"]:
            with self.subTest(connection=connection):
                self.assertEqual(
                    connection.get("no_connect", False), len(connection["pads"]) == 1
                )

    def test_every_placed_part_resolves_to_an_approved_product(self):
        design = json.loads((PCB / "design/netlist.json").read_text())
        for reference, component in design["projects"]["board"]["components"].items():
            with self.subTest(reference=reference):
                spec = COMPONENTS[component["part_key"]]
                self.assertEqual(component["package"], spec.package)

    def test_native_schematic_and_symbol_library_are_current(self):
        schematic = render_schematic()
        self.assertEqual((PCB / "chess-board.kicad_sch").read_text(), schematic)
        self.assertEqual(
            (PCB / "generated-symbols.kicad_sym").read_text(),
            render_symbol_library(schematic),
        )

    def test_approved_bodies_fit_their_footprint_courtyards(self):
        for spec in COMPONENTS.values():
            if spec.body_mm is None or spec.package not in footprints.CATALOG:
                continue
            body = sorted(spec.body_mm[:2])
            courtyard = sorted(footprints.CATALOG[spec.package].courtyard)
            with self.subTest(part=spec.key):
                self.assertGreaterEqual(courtyard[0], body[0])
                self.assertGreaterEqual(courtyard[1], body[1])

    def test_the_project_has_no_drc_exclusions(self):
        project = json.loads((PCB / "chess-board.kicad_pro").read_text())
        settings = project["board"]["design_settings"]
        self.assertEqual(settings.get("drc_exclusions", []), [])
        self.assertNotIn("ignore", settings["rule_severities"].values())

    def test_completed_routing_subsystems_stay_complete(self):
        drc = json.loads((PCB / "generated/drc.json").read_text())
        self.assertEqual(drc["violations"], [])
        self.assertEqual(drc["unconnected_items"], [])
        self.assertEqual(drc["schematic_parity"], [])
        descriptions = "\n".join(
            item["description"]
            for violation in drc["unconnected_items"]
            for item in violation["items"]
        )
        for routed_prefix in ("[SQ_", "[LED_", "[SPI_", "[DC_"):
            with self.subTest(prefix=routed_prefix):
                self.assertNotIn(routed_prefix, descriptions)
        self.assertFalse(any("[N$" in line for line in descriptions.splitlines()))

    def test_machine_audit_covers_every_release_dimension(self):
        report = board_audit.audit()
        self.assertEqual(report["unknown_part_keys"], [])
        self.assertEqual(report["package_mismatches"], [])
        self.assertEqual(report["implicit_no_connects"], 0)
        self.assertTrue(report["bom_current"])
        self.assertEqual(report["drc_exclusions"], 0)
        self.assertEqual(report["ignored_drc_rules"], [])
        self.assertEqual(report["erc_violations"], 0)
        self.assertEqual(report["drc_violations"], 0)
        self.assertEqual(report["unconnected_items"], 0)
        self.assertEqual(report["schematic_parity_errors"], 0)

    def test_the_runner_enforces_the_release_gate_before_gerbers(self):
        runner = (PCB.parents[1] / "tools/pcb").read_text()
        review_only = runner.index("PCB_REVIEW_ONLY:-0")
        gate = runner.index("validate_release.py")
        fabrication = runner.index("pcb export gerbers")
        self.assertLess(review_only, gate)
        self.assertLess(gate, fabrication)
        self.assertIn("--severity-exclusions", runner)
        workflow = (PCB.parents[1] / ".github/workflows/ci.yml").read_text()
        self.assertIn("env PCB_REVIEW_ONLY=1 ./tools/pcb", workflow)


if __name__ == "__main__":
    unittest.main()
