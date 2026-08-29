"""Tests for electronics generator ownership, reuse, and runner ordering."""

from pathlib import Path
import unittest


REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
ELECTRONICS_ROOT = REPOSITORY_ROOT / "hardware" / "electronics"
PROJECTS = ELECTRONICS_ROOT / "projects"


class GeneratorStructureTest(unittest.TestCase):
    def test_projects_declare_dependency_order(self) -> None:
        ranked = []
        for generate in PROJECTS.glob("*/generate.py"):
            order_file = generate.parent / "generation-order"
            order = 100
            if order_file.is_file():
                order = int(order_file.read_text().splitlines()[0])
            ranked.append((order, str(generate.relative_to(REPOSITORY_ROOT))))
        ranked.sort()
        self.assertEqual(
            [path for _, path in ranked],
            [
                "hardware/electronics/projects/square/generate.py",
                "hardware/electronics/projects/chessboard/generate.py",
            ],
        )

    def test_every_schematic_has_one_owning_generator(self) -> None:
        ownership = {
            "Chess Smart Board - Single Square": PROJECTS / "square" / "generate.py",
            "Chess Smart Board - Complete Electronics": PROJECTS
            / "chessboard"
            / "generate.py",
        }
        generator_text = {path: path.read_text() for path in set(ownership.values())}
        for title, owner in ownership.items():
            with self.subTest(title=title):
                self.assertIn(f'"{title}"', generator_text[owner])
                other_text = "\n".join(
                    text for path, text in generator_text.items() if path != owner
                )
                self.assertNotIn(f'"{title}"', other_text)

    def test_projects_use_shared_blocks_without_a_sheet_registry(self) -> None:
        square = (PROJECTS / "square" / "generate.py").read_text()
        chessboard = (PROJECTS / "chessboard" / "generate.py").read_text()
        self.assertIn("from blocks.square import", square)
        self.assertIn("from blocks.leds import", chessboard)
        self.assertIn("sys.path.insert(0, str(ELECTRONICS_ROOT))", square)
        self.assertIn("sys.path.insert(0, str(ELECTRONICS_ROOT))", chessboard)
        self.assertNotIn("SHEETS", square)
        self.assertNotIn("SHEETS", chessboard)

    def test_single_components_live_one_per_module(self) -> None:
        components = ELECTRONICS_ROOT / "components"
        modules = {path.stem for path in components.glob("*.py")}
        self.assertIn("ws2812b", modules)
        self.assertIn("pico_2w", modules)
        self.assertIn("reed_switch", modules)
        # Composition belongs to blocks and project generators, not the catalog.
        for path in components.glob("*.py"):
            self.assertNotIn("def add_", path.read_text(), path.name)

    def test_the_main_directory_holds_no_artefacts(self) -> None:
        """Generated output belongs in generated/, not loose beside the source."""
        loose = {path.name for path in ELECTRONICS_ROOT.iterdir() if path.is_file()}
        self.assertEqual(loose, {"README.md", "requirements.txt"})
        self.assertTrue((ELECTRONICS_ROOT / "generated").is_dir())

    def test_the_domain_keeps_the_shared_directory_shape(self) -> None:
        """Both hardware domains present the same directories to a reader."""
        directories = {
            path.name
            for path in ELECTRONICS_ROOT.iterdir()
            if path.is_dir() and path.name != "__pycache__"
        }
        self.assertEqual(
            directories,
            {
                "blocks",
                "components",
                "core",
                "generated",
                "projects",
                "prototype",
                "tests",
            },
        )

    def test_legacy_layout_is_removed(self) -> None:
        self.assertFalse((ELECTRONICS_ROOT / "chessboard").exists())
        self.assertFalse((ELECTRONICS_ROOT / "square").exists())
        self.assertFalse((ELECTRONICS_ROOT / "renders").exists())
        self.assertFalse((ELECTRONICS_ROOT / "kicad").exists())
        square = (PROJECTS / "square" / "generate.py").read_text()
        chessboard = (PROJECTS / "chessboard" / "generate.py").read_text()
        self.assertIn(
            "hardware/electronics/projects/square/generate.py", square
        )
        self.assertIn(
            "hardware/electronics/projects/chessboard/generate.py", chessboard
        )
        self.assertNotIn("hardware/electronics/square/generate.py", square)
        self.assertNotIn(
            "hardware/electronics/chessboard/generate.py", chessboard
        )

    def test_runner_rebuilds_the_bill_of_materials_after_generating(self) -> None:
        runner = (REPOSITORY_ROOT / "tools" / "electronics").read_text()
        self.assertIn("core/bom.py", runner)


class ComponentCatalogTest(unittest.TestCase):
    """A new part is a new module; nothing else should need editing."""

    def test_catalog_registers_every_module_without_an_import_list(self) -> None:
        import sys

        if str(ELECTRONICS_ROOT) not in sys.path:
            sys.path.insert(0, str(ELECTRONICS_ROOT))
        import components

        modules = {
            path.stem
            for path in (ELECTRONICS_ROOT / "components").glob("*.py")
            if path.stem not in {"__init__", "base"}
        }
        self.assertTrue(modules)
        self.assertGreaterEqual(len(components.CATALOG), len(modules))
        for part in components.CATALOG.values():
            self.assertTrue(part.package, part.lib)
            self.assertTrue(part.description, part.lib)
            self.assertTrue(callable(part.build), part.lib)
        source = (ELECTRONICS_ROOT / "components" / "__init__.py").read_text()
        for module in modules:
            self.assertNotIn(f"from .{module} import", source, module)

    def test_a_new_module_is_picked_up_with_no_other_edits(self) -> None:
        import importlib
        import sys

        if str(ELECTRONICS_ROOT) not in sys.path:
            sys.path.insert(0, str(ELECTRONICS_ROOT))
        probe = ELECTRONICS_ROOT / "components" / "_probe_part.py"
        probe.write_text(
            "from schemdraw import elements as elm\n"
            "from .base import TWO_TERMINAL, Component\n\n"
            "PROBE = Component(\n"
            '    lib="PROBE",\n'
            '    value="1k",\n'
            '    description="Temporary catalog probe",\n'
            '    package="0603",\n'
            "    build=lambda: elm.Resistor().right(),\n"
            "    pins=TWO_TERMINAL,\n"
            ")\n"
        )
        try:
            import components

            importlib.reload(components)
            self.assertIn("PROBE", components.CATALOG)
            self.assertEqual(components.CATALOG["PROBE"].value, "1k")
        finally:
            probe.unlink()
            import components

            importlib.reload(components)
        self.assertNotIn("PROBE", components.CATALOG)


if __name__ == "__main__":
    unittest.main()
