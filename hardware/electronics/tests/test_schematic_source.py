"""Schemdraw source-of-truth checks for generated drawings and topology."""

from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path
from types import ModuleType

ELECTRONICS = Path(__file__).resolve().parents[1]
PROJECTS = ELECTRONICS / "projects"
GENERATED = ELECTRONICS / "generated"
BOM = GENERATED / "bom.md"
CHESSBOARD_SVG = GENERATED / "chessboard.svg"
SQUARE_SVG = GENERATED / "square.svg"
SQUARES = [f"{file_}{rank}" for file_ in "ABCDEFGH" for rank in range(1, 9)]


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
        cls.sch = load_generator("chessboard").assemble()
        cls.source = CHESSBOARD_SVG.read_text() if CHESSBOARD_SVG.is_file() else ""

    def test_python_is_the_source_of_truth(self) -> None:
        generator = PROJECTS / "chessboard" / "generate.py"
        self.assertTrue(generator.is_file())
        self.assertIn("complete chessboard schematic", generator.read_text())
        self.assertFalse((ELECTRONICS.parents[1] / "tools" / "chess_electronics.py").exists())
        self.assertTrue((ELECTRONICS / "blocks" / "square.py").is_file())
        self.assertTrue((ELECTRONICS / "components" / "__init__.py").is_file())
        self.assertTrue((PROJECTS / "square" / "generate.py").is_file())
        self.assertFalse((ELECTRONICS / "generate.py").exists())
        self.assertFalse((ELECTRONICS / "design").exists())
        self.assertFalse((ELECTRONICS / "kicad").exists())
        self.assertFalse((ELECTRONICS / "layout.py").exists())
        self.assertFalse((ELECTRONICS / "canvas.py").exists())

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
        self.assertEqual(libs.count("DIODE"), 64)
        self.assertEqual(libs.count("WS2812B"), 64)
        self.assertEqual(libs.count("PICO_2_W"), 1)
        self.assertEqual(libs.count("AHCT125"), 1)

    def test_all_board_squares_are_mapped(self) -> None:
        squares = {
            spec.extras["Square"]
            for spec in self.sch.symbols
            if "Square" in spec.extras
        }
        self.assertEqual(squares, set(SQUARES))

    def test_controller_assignment_is_documented_on_the_sheet(self) -> None:
        self.assertIn("GP1-GP8 rows", self.source)
        self.assertIn("GP9-GP16 columns", self.source)
        self.assertIn("GP0 LED data", self.source)
        self.assertIn("GP26 battery ADC", self.source)

    def test_matrix_and_led_harness_are_drawn(self) -> None:
        labels = self.sch.labels
        for index in range(8):
            self.assertIn(f"ROW_{index}", labels)
            self.assertIn(f"COL_{index}", labels)
        self.assertIn("LED_DATA_CHAIN", labels)
        self.assertIn("LED_DOUT_LAST", labels)

    def test_renders_live_together_in_the_generated_folder(self) -> None:
        published = {path.name for path in GENERATED.iterdir()} - {"README.md"}
        self.assertEqual(
            published,
            {
                "chessboard.svg",
                "chessboard.png",
                "square.svg",
                "square.png",
                "bom.md",
            },
        )
        for project in ("chessboard", "square"):
            self.assertFalse((PROJECTS / project / "generated").exists(), project)

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
        before = SQUARE_SVG.read_text()
        load_generator("square").build()
        self.assertEqual(SQUARE_SVG.read_text(), before)

    def test_component_list_is_generated_with_quantities(self) -> None:
        text = BOM.read_text()
        self.assertIn("do not edit by hand", text)
        # Counted from the drawing, and consecutive references collapse to a span.
        self.assertIn("| 64 | WS2812B | PLCC-4 5 mm |", text)
        self.assertIn("SW2-SW65", text)
        self.assertIn("| 8 | 10k | 0603 | Matrix column pull-up to 3.3 V |", text)
        self.assertIn("### To order", text)
        # Identical parts from different circuits merge for ordering.
        self.assertIn("| 66 | 100nF | 0603 |", text)
        self.assertIn("Loop test point", text)

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
            and ("kicad" in path.name.lower() or path.suffix in {".kicad_sch", ".kicad_pro", ".kicad_sym"})
        ]
        self.assertEqual(leftovers, [])


class SquareSheetTest(unittest.TestCase):
    def test_single_square_population(self) -> None:
        sch = load_generator("square").assemble()
        libs = [spec.lib for spec in sch.symbols]
        self.assertEqual(libs.count("REED"), 1)
        self.assertEqual(libs.count("DIODE"), 1)
        self.assertEqual(libs.count("WS2812B"), 1)
        self.assertIn("ROW_0", sch.labels)
        self.assertIn("COL_0", sch.labels)
        self.assertIn("LED_DIN", sch.labels)
        self.assertIn("LED_DOUT", sch.labels)
        self.assertIn("Chess Smart Board - Single Square", SQUARE_SVG.read_text())


if __name__ == "__main__":
    unittest.main()
