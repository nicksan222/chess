"""Schemdraw source-of-truth checks, plus the hand-assembly guardrails."""

from __future__ import annotations

import importlib.util
import re
import sys
import unittest
from pathlib import Path
from types import ModuleType

ELECTRONICS = Path(__file__).resolve().parents[1]
PROJECTS = ELECTRONICS / "projects"
GENERATED = ELECTRONICS / "generated"
BOM = GENERATED / "bom.md"
BOARD_SVG = GENERATED / "board.svg"
SQUARES = [f"{file_}{rank}" for file_ in "ABCDEFGH" for rank in range(1, 9)]

# Anything matching these is a surface-mount package a hand assembler cannot
# comfortably place. The LED is the design's one accepted exception.
SURFACE_MOUNT = re.compile(
    r"\b(0402|0603|0805|1206|SOT-|SOD-|SMA|SMB|SMC|QFN|QFP|TSSOP|MSOP|SO-\d+|SOIC)",
    re.IGNORECASE,
)
SURFACE_MOUNT_EXCEPTIONS = {"SK9822"}
MAX_PURCHASE_LINES = 20


def load_generator(project: str) -> ModuleType:
    path = PROJECTS / project / "generate.py"
    spec = importlib.util.spec_from_file_location(f"electronics_{project}_generate", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class SchematicSourceTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.sch = load_generator("board").assemble()
        cls.source = BOARD_SVG.read_text() if BOARD_SVG.is_file() else ""

    def test_python_is_the_source_of_truth(self) -> None:
        generator = PROJECTS / "board" / "generate.py"
        self.assertTrue(generator.is_file())
        self.assertIn("single-board schematic", generator.read_text())
        self.assertTrue((ELECTRONICS / "components" / "__init__.py").is_file())
        self.assertFalse((ELECTRONICS / "generate.py").exists())
        self.assertFalse((ELECTRONICS / "kicad").exists())
        self.assertFalse((ELECTRONICS / "layout.py").exists())

    def test_schemdraw_is_the_drawing_library(self) -> None:
        canvas = (ELECTRONICS / "core" / "canvas.py").read_text()
        self.assertIn("import schemdraw", canvas)
        self.assertNotIn("kicad", canvas.lower())
        sources = "\n".join(
            path.read_text()
            for path in sorted(ELECTRONICS.rglob("*.py"))
            if "tests" not in path.parts
        ).lower()
        for forbidden in ("kicad_sch_api", "skidl", "kiutils", "sexpdata", "kicad_sch"):
            self.assertNotIn(forbidden, sources, forbidden)

    def test_complete_component_population(self) -> None:
        libs = [spec.lib for spec in self.sch.symbols]
        self.assertEqual(libs.count("REED"), 64)
        self.assertEqual(libs.count("SK9822"), 64)
        self.assertEqual(libs.count("MCP23017"), 4)
        self.assertEqual(libs.count("AHCT125"), 1)
        self.assertEqual(libs.count("BUTTON"), 12)
        self.assertEqual(libs.count("PI_HEADER"), 1)
        self.assertEqual(libs.count("OLED_HEADER"), 1)
        # Four chip sockets plus one for the buffer.
        self.assertEqual(libs.count("DIP_SOCKET"), 5)

    def test_the_replaced_revision_a_parts_are_gone(self) -> None:
        libs = {spec.lib for spec in self.sch.symbols}
        for absent in ("PICO_2_W", "WS2812B", "BATTERY", "BUCK", "DIODE"):
            self.assertNotIn(absent, libs, absent)

    def test_only_the_leds_are_surface_mount(self) -> None:
        """The board has to be assemblable by hand at a kitchen table."""
        offenders = sorted(
            {
                f"{spec.value} ({spec.package})"
                for spec in self.sch.symbols
                if SURFACE_MOUNT.search(spec.package)
                and spec.value not in SURFACE_MOUNT_EXCEPTIONS
            }
        )
        self.assertEqual(offenders, [])

    def test_both_integrated_circuits_sit_in_sockets(self) -> None:
        chips = {
            spec.value
            for spec in self.sch.symbols
            if spec.package.upper().startswith(("DIP-", "PDIP-"))
            and "socket" not in spec.value.lower()
        }
        self.assertEqual(chips, {"MCP23017-E/SP", "SN74AHCT125N"})
        sockets = sum(1 for spec in self.sch.symbols if spec.lib == "DIP_SOCKET")
        self.assertEqual(sockets, len([s for s in self.sch.symbols if s.value in chips]))

    def test_all_board_squares_are_mapped(self) -> None:
        squares = {
            spec.extras["Square"]
            for spec in self.sch.symbols
            if "Square" in spec.extras
        }
        self.assertEqual(squares, set(SQUARES))

    def test_the_sheet_documents_why_the_buffer_exists(self) -> None:
        self.assertIn("SK9822 needs", self.source)
        self.assertIn("No regulator on board", self.source)

    def test_signal_names_are_drawn(self) -> None:
        labels = self.sch.labels
        for square in ("SQ_A1", "SQ_H8", "SQ_E4"):
            self.assertIn(square, labels)
        for net in ("I2C_SDA", "I2C_SCL", "SENSE_IRQ", "LED_DATA_5V", "LED_CLK_5V"):
            self.assertIn(net, labels)
        for button in ("BTN_UP", "BTN_OK", "BTN_RESET", "BTN_PASS", "BTN_F5"):
            self.assertIn(button, labels)

    def test_renders_live_together_in_the_generated_folder(self) -> None:
        published = {path.name for path in GENERATED.iterdir()} - {"README.md"}
        self.assertEqual(
            published, {"board.svg", "board.png", "bom.md", "netlist.json"}
        )
        self.assertFalse((PROJECTS / "board" / "generated").exists())

    def test_the_netlist_is_published_for_the_fabrication_domain(self) -> None:
        """`hardware/pcb` consumes this instead of importing Schemdraw."""
        import json

        published = json.loads((GENERATED / "netlist.json").read_text())
        board = published["projects"]["board"]
        self.assertEqual(published["schema"], 1)
        # Every component carries the package its footprint is looked up by.
        self.assertEqual(len(board["components"]), len(self.sch.symbols))
        for reference, entry in board["components"].items():
            self.assertTrue(entry["package"], reference)
        # Per-square parts carry their square, so they can be placed on a grid.
        squares = {
            entry["extras"]["Square"]
            for entry in board["components"].values()
            if "Square" in entry["extras"]
        }
        self.assertEqual(squares, set(SQUARES))
        self.assertEqual(board["nets"]["SQ_A1"], sorted(board["nets"]["SQ_A1"]))

    def test_generated_drawings_carry_no_trailing_whitespace(self) -> None:
        """The repository's pre-commit check rejects it, generated or not."""
        for path in sorted(GENERATED.glob("*.svg")):
            offenders = [
                number
                for number, line in enumerate(path.read_text().splitlines(), 1)
                if line != line.rstrip()
            ]
            self.assertEqual(offenders[:5], [], path.name)

    def test_rebuilding_a_drawing_changes_nothing(self) -> None:
        """A committed artefact must not churn on every build."""
        before = BOARD_SVG.read_text()
        load_generator("board").build()
        self.assertEqual(BOARD_SVG.read_text(), before)

    def test_component_list_is_generated_with_quantities(self) -> None:
        text = BOM.read_text()
        self.assertIn("do not edit by hand", text)
        # Counted from the drawing, and consecutive references collapse to a span.
        self.assertIn("| 64 | SK9822 | PLCC-6 5050 |", text)
        self.assertIn("RS1-RS64", text)
        self.assertIn("| 4 | MCP23017-E/SP | PDIP-28 |", text)
        self.assertIn("| 12 | TACT 6mm | 6x6 mm THT |", text)
        self.assertIn("### To order", text)
        # Identical parts from different circuits merge for ordering.
        self.assertIn("| 69 | 100nF | disc 2.54 mm |", text)

    def test_the_order_stays_short_enough_to_review(self) -> None:
        order = BOM.read_text().split("### To order", 1)[1]
        lines = [line for line in order.splitlines() if re.match(r"^\| \d+ \|", line)]
        self.assertLessEqual(len(lines), MAX_PURCHASE_LINES, "\n".join(lines))

    def test_component_counts_match_the_schematic(self) -> None:
        from core import bom

        rows = bom.lines(self.sch)
        self.assertEqual(sum(row.quantity for row in rows), len(self.sch.symbols))
        reeds = next(row for row in rows if row.value == "REED NO")
        self.assertEqual(reeds.quantity, 64)

    def test_no_kicad_artifacts_remain(self) -> None:
        leftovers = [
            str(path.relative_to(ELECTRONICS))
            for path in ELECTRONICS.rglob("*")
            if path.is_file()
            and "__pycache__" not in path.parts
            and (
                "kicad" in path.name.lower()
                or path.suffix in {".kicad_sch", ".kicad_pro", ".kicad_sym"}
            )
        ]
        self.assertEqual(leftovers, [])


if __name__ == "__main__":
    unittest.main()
