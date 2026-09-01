"""Fabrication cannot bypass connectivity or KiCad's native checks."""

import json
import unittest
from pathlib import Path

from base import rules
from board import definition as board_definition
from components import footprints
from configure_project import render as render_project
from shared.components import COMPONENTS
from write_bom import render as render_bom
from write_bom import render_assembly_csv
from write_schematic import render as render_schematic
from write_schematic import render_symbol_library, row_centres

PCB = Path(__file__).resolve().parents[1]


class ReleasePolicyTest(unittest.TestCase):
    def test_every_single_pad_group_is_an_explicit_no_connect(self):
        design = json.loads((PCB / "board/netlist.json").read_text())
        for connection in design["projects"]["board"]["connections"]:
            with self.subTest(connection=connection):
                self.assertEqual(
                    connection.get("no_connect", False), len(connection["pads"]) == 1
                )

    def test_every_placed_part_resolves_to_an_approved_product(self):
        design = json.loads((PCB / "board/netlist.json").read_text())
        for reference, component in design["projects"]["board"]["components"].items():
            with self.subTest(reference=reference):
                spec = COMPONENTS[component["part_key"]]
                self.assertEqual(component["package"], spec.package)
                self.assertTrue(spec.manufacturer.strip())
                self.assertTrue(spec.mpn.strip())
                self.assertNotEqual(spec.manufacturer.casefold(), "generic")
                self.assertNotEqual(spec.mpn, spec.key)

    def test_schematic_rows_expand_for_tall_symbols(self):
        self.assertEqual(row_centres([]), [])
        centres = row_centres([2] * 20 + [28] + [2] * 19)
        self.assertEqual(len(centres), 2)
        self.assertGreater(centres[1] - centres[0], 40.0)

    def test_native_schematic_and_symbol_library_are_current(self):
        design = board_definition.load()
        schematic = render_schematic(design)
        self.assertIn(f'(title "{design.title}")', schematic)
        self.assertIn(f'(rev "{design.revision}")', schematic)
        self.assertEqual(
            (PCB / "generated/chess-board.kicad_sch").read_text(), schematic
        )
        self.assertEqual(
            (PCB / "generated/generated-symbols.kicad_sym").read_text(),
            render_symbol_library(schematic),
        )

    def test_generated_boms_are_current(self):
        self.assertEqual((PCB / "generated/bom.md").read_text(), render_bom())
        self.assertEqual(
            (PCB / "generated/assembly-bom.csv").read_text(),
            render_assembly_csv(),
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

    def test_generated_project_is_current_and_has_no_drc_exclusions(self):
        project_text = (PCB / "generated/chess-board.kicad_pro").read_text()
        self.assertEqual(project_text, render_project())
        project = json.loads(project_text)
        settings = project["board"]["design_settings"]
        defaults = settings["defaults"]
        constraints = settings["rules"]
        self.assertEqual(defaults["board_outline_line_width"], rules.OUTLINE_LINE_MM)
        self.assertEqual(defaults["courtyard_line_width"], rules.COURTYARD_LINE_MM)
        self.assertEqual(defaults["fab_line_width"], rules.FAB_LINE_MM)
        self.assertEqual(defaults["silk_line_width"], rules.SILK_LINE_MM)
        self.assertEqual(defaults["silk_text_size_h"], rules.SILK_TEXT_HEIGHT_MM)
        self.assertEqual(defaults["silk_text_size_v"], rules.SILK_TEXT_HEIGHT_MM)
        self.assertEqual(defaults["silk_text_thickness"], rules.SILK_LINE_MM)
        self.assertEqual(defaults["zones"]["min_clearance"], rules.POUR_CLEARANCE_MM)
        self.assertEqual(constraints["min_clearance"], rules.CLEARANCE_MM)
        self.assertEqual(
            constraints["min_copper_edge_clearance"], rules.POUR_TO_OUTLINE_MM
        )
        self.assertEqual(constraints["min_hole_clearance"], rules.HOLE_CLEARANCE_MM)
        self.assertEqual(constraints["min_hole_to_hole"], rules.HOLE_TO_HOLE_MM)
        self.assertEqual(constraints["min_track_width"], rules.TRACE_WIDTH_MM)
        self.assertEqual(constraints["min_via_diameter"], rules.VIA_PAD_MM)
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

    def test_native_erc_is_clean(self):
        erc = json.loads((PCB / "generated/erc.json").read_text())
        violations = [
            violation
            for sheet in erc.get("sheets", [])
            for violation in sheet.get("violations", [])
        ]
        self.assertEqual(violations, [])

    def test_pcb_makefile_keeps_common_operations_inside_the_container(self):
        makefile = (PCB / "Makefile").read_text()
        for target in (
            "test",
            "component-check",
            "bom",
            "schematic",
            "board",
            "review",
            "release",
            "check",
        ):
            with self.subTest(target=target):
                recipe = makefile.split(f"{target}:", 1)[1].split("\n\n", 1)[0]
                self.assertIn("$(DC)", recipe)
        self.assertIn("release: up", makefile)
        self.assertIn("$(DC) ./tools/pcb", makefile)
        self.assertIn("PCB_REVIEW_ONLY=1 ./tools/pcb", makefile)

    def test_the_runner_enforces_the_release_gate_before_gerbers(self):
        runner = (PCB.parents[1] / "tools/pcb").read_text()
        review_only = runner.index("PCB_REVIEW_ONLY:-0")
        gate = runner.index("PCB_RELEASE=1")
        fabrication = runner.index("pcb export gerbers")
        self.assertLess(review_only, gate)
        self.assertLess(gate, fabrication)
        self.assertIn("python3 -m unittest discover", runner)
        self.assertIn("--severity-exclusions", runner)
        workflow = (PCB.parents[1] / ".github/workflows/ci.yml").read_text()
        self.assertIn("env PCB_REVIEW_ONLY=1 ./tools/pcb", workflow)


if __name__ == "__main__":
    unittest.main()
