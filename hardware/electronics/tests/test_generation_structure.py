"""Tests for electronics generator ownership, reuse, and runner ordering."""

from pathlib import Path
import unittest


REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
ELECTRONICS_ROOT = REPOSITORY_ROOT / "hardware" / "electronics"
PROJECTS = ELECTRONICS_ROOT / "projects"
BLOCKS = ELECTRONICS_ROOT / "blocks"


class GeneratorStructureTest(unittest.TestCase):
    def test_one_board_means_one_generator(self) -> None:
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
            ["hardware/electronics/projects/board/generate.py"],
        )

    def test_the_sheet_has_one_owning_generator(self) -> None:
        generator = (PROJECTS / "board" / "generate.py").read_text()
        self.assertIn('"Chess Smart Board - Single Board Electronics"', generator)

    def test_the_project_composes_shared_blocks_without_a_registry(self) -> None:
        board = (PROJECTS / "board" / "generate.py").read_text()
        for block in (
            "blocks.control_panel",
            "blocks.host_interface",
            "blocks.leds",
            "blocks.power",
            "blocks.sensing",
        ):
            self.assertIn(f"from {block} import", board, block)
        self.assertIn("sys.path.insert(0, str(ELECTRONICS_ROOT))", board)
        self.assertNotIn("SHEETS", board)

    def test_blocks_are_the_only_place_composition_lives(self) -> None:
        self.assertEqual(
            {path.stem for path in BLOCKS.glob("*.py")} - {"__init__"},
            {"control_panel", "host_interface", "leds", "power", "sensing"},
        )

    def test_single_components_live_one_per_module(self) -> None:
        components = ELECTRONICS_ROOT / "components"
        modules = {path.stem for path in components.glob("*.py")}
        for expected in (
            "sk9822",
            "i2c_expander",
            "level_buffer",
            "pi_header",
            "oled_header",
            "button",
            "barrel_jack",
            "dip_socket",
            "reed_switch",
        ):
            self.assertIn(expected, modules, expected)
        # Composition belongs to blocks and project generators, not the catalog.
        for path in components.glob("*.py"):
            self.assertNotIn("def add_", path.read_text(), path.name)

    def test_revision_a_parts_are_deleted_not_left_unused(self) -> None:
        components = ELECTRONICS_ROOT / "components"
        for gone in (
            "pico_2w",
            "ws2812b",
            "battery",
            "buck_regulator",
            "level_shifter",
            "diode",
        ):
            self.assertFalse((components / f"{gone}.py").exists(), gone)

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
        for gone in ("chessboard", "square", "renders", "kicad"):
            self.assertFalse((ELECTRONICS_ROOT / gone).exists(), gone)
            self.assertFalse((PROJECTS / gone).exists(), gone)
        board = (PROJECTS / "board" / "generate.py").read_text()
        self.assertIn("hardware/electronics/projects/board/generate.py", board)

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
            '    package="axial 1/4 W",\n'
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
