"""Executable electrical and manufacturing release requirements."""

from __future__ import annotations

import csv
import json
import os
import unittest
from pathlib import Path

from shared.components import BARREL_JACK, FUSE_2A, OLED_MODULE, POWER_SUPPLY

PCB = Path(__file__).resolve().parents[2]
GENERATED = PCB / "generated"


class ProductSelectionTest(unittest.TestCase):
    def test_display_is_a_real_four_wire_module_matching_the_panel(self):
        self.assertEqual(OLED_MODULE.manufacturer, "AZ-Delivery")
        self.assertEqual(OLED_MODULE.mpn, "A 1-6")
        self.assertEqual(OLED_MODULE.package, "36x34 mm module")
        self.assertIn("SH1106", OLED_MODULE.description)
        self.assertIn("four-pin", OLED_MODULE.description)
        self.assertTrue(OLED_MODULE.datasheet.startswith("https://"))

    def test_input_products_stay_inside_the_jack_rating(self):
        self.assertEqual(BARREL_JACK.mpn, "PJ-102A")
        self.assertIn("2.5 A rated", BARREL_JACK.description)
        self.assertEqual(FUSE_2A.mpn, "0453002.MR")
        self.assertIn("2 A", FUSE_2A.description)
        self.assertEqual(POWER_SUPPLY.mpn, "GST12A05-P1J")
        self.assertIn("5 V 2 A", POWER_SUPPLY.description)


class ElectricalReadinessTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.board = json.loads((PCB / "board/data/netlist.json").read_text())[
            "projects"
        ]["board"]
        cls.connections = {
            connection["name"]: connection
            for connection in cls.board["connections"]
            if connection["name"] is not None
        }

    def test_polled_sensors_have_no_global_irq_circuit(self):
        self.assertNotIn("SENSE_IRQ", self.connections)
        self.assertNotIn("R3", self.board["components"])
        self.assertNotIn("TP8", self.board["components"])
        no_connects = {
            tuple(c["pads"][0])
            for c in self.board["connections"]
            if c.get("no_connect")
        }
        self.assertIn(("J1", "7"), no_connects)
        for ref, component in self.board["components"].items():
            if component["part_key"] == "TCA9554":
                self.assertIn((ref, "13"), no_connects)

    def test_bring_up_points_cover_rails_buses_and_led_input(self):
        expected = {
            "TP1": "+5V",
            "TP2": "GND",
            "TP3": "LED_DATA_5V",
            "TP4": "LED_CLK_5V",
            "TP5": "+3V3",
            "TP6": "I2C_SCL",
            "TP7": "I2C_SDA",
        }
        attached = {
            endpoint[0]: name
            for name, connection in self.connections.items()
            for endpoint in connection["pads"]
            if endpoint[0].startswith("TP")
        }
        self.assertEqual(attached, expected)

    def test_power_limit_and_pcbway_order_requirements_are_recorded(self):
        manufacturing = json.loads((PCB / "board/data/manufacturing.json").read_text())
        self.assertEqual(
            manufacturing["power"]["led_global_brightness_max"],
            "3/31",
        )
        fabrication = manufacturing["fabrication"]
        self.assertEqual(fabrication["board_size_mm"], [320.0, 360.0])
        self.assertEqual(fabrication["plated_component_slot_mm"], [1.0, 1.6])
        self.assertIs(fabrication["controlled_impedance"], False)


@unittest.skipUnless(
    os.environ.get("PCB_RELEASE") == "1",
    "physical evidence is required only by the fabrication release suite",
)
class PhysicalReleaseEvidenceTest(unittest.TestCase):
    def test_hall_sensor_operates_with_both_magnet_poles_at_final_spacing(self):
        evidence_path = PCB / "board/prototype/hall-magnet.json"
        self.assertTrue(evidence_path.is_file(), f"missing {evidence_path}")
        record = json.loads(evidence_path.read_text())
        self.assertEqual(record.get("schema"), 1)
        self.assertEqual(record.get("board_revision"), "D-PROTOTYPE")
        self.assertEqual(record.get("sensor_mpn"), "DRV5032FCDBZR")
        self.assertIs(record.get("pass"), True)
        final_gap = record.get("final_gap_mm")
        self.assertIsInstance(final_gap, (int, float))
        self.assertGreater(final_gap, 0)
        for pole in ("north", "south"):
            measurements = record.get(pole)
            self.assertIsInstance(measurements, dict)
            for name in ("operate_mm", "release_mm"):
                values = measurements.get(name)
                self.assertIsInstance(values, list)
                self.assertGreaterEqual(len(values), 5)
                self.assertTrue(
                    all(
                        isinstance(value, (int, float)) and value > 0
                        for value in values
                    )
                )
            self.assertGreaterEqual(min(measurements["operate_mm"]), final_gap + 0.5)
        self.assertTrue(str(record.get("notes", "")).strip())


class GeneratedOutputPolicyTest(unittest.TestCase):
    def test_no_generated_kicad_files_live_in_the_source_root(self):
        forbidden = (
            "*.kicad_pcb",
            "*.kicad_pro",
            "*.kicad_sch",
            "*.kicad_prl",
            "*.kicad_sym",
            "sym-lib-table",
        )
        found = sorted(path.name for pattern in forbidden for path in PCB.glob(pattern))
        self.assertEqual(found, [])

    def test_complete_native_project_lives_under_generated(self):
        required = {
            "chess-board.kicad_pcb",
            "chess-board.kicad_pro",
            "chess-board.kicad_sch",
            "generated-symbols.kicad_sym",
            "sym-lib-table",
            "bom.md",
            "assembly-bom.csv",
            "positions.csv",
            "drc.json",
            "erc.json",
        }
        self.assertEqual(
            sorted(name for name in required if not (GENERATED / name).is_file()),
            [],
        )

    def test_pick_and_place_excludes_mechanical_hole_footprints(self):
        with (GENERATED / "positions.csv").open(newline="") as source:
            references = {row["Ref"] for row in csv.DictReader(source)}
        self.assertFalse(
            any(ref[1:].isdigit() for ref in references if ref.startswith("H"))
        )


if __name__ == "__main__":
    unittest.main()
