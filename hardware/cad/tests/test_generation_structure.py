"""Tests for CAD generator ownership, reuse, and main-runner ordering."""

import unittest
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
CAD_ROOT = REPOSITORY_ROOT / "hardware" / "cad"
PROJECTS = CAD_ROOT / "projects"
GENERATED = CAD_ROOT / "generated"
BLOCKS = CAD_ROOT / "blocks"

PRINTABLE_PROJECTS = ("board-case", "tile-plate")
VIEW_PROJECTS = ("board-assembly",)


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
                "hardware/cad/projects/board-case/generate.py",
                "hardware/cad/projects/tile-plate/generate.py",
                "hardware/cad/projects/board-assembly/generate.py",
            ],
        )

    def test_every_printable_model_has_one_owning_generator(self) -> None:
        ownership = {
            "Printable_Board_Case": PROJECTS / "board-case" / "generate.py",
            "Printable_Tile_Plate": PROJECTS / "tile-plate" / "generate.py",
        }
        generator_text = {path: path.read_text() for path in set(ownership.values())}
        for object_name, owner in ownership.items():
            with self.subTest(object_name=object_name):
                self.assertIn(f'"{object_name}"', generator_text[owner])
                other_text = "\n".join(
                    text for path, text in generator_text.items() if path != owner
                )
                self.assertNotIn(f'"{object_name}"', other_text)

    def test_the_board_is_two_printed_parts(self) -> None:
        self.assertEqual(
            {path.parent.name for path in PROJECTS.glob("*/generate.py")},
            set(PRINTABLE_PROJECTS) | set(VIEW_PROJECTS),
        )

    def test_views_import_printable_sources_without_redefining_them(self) -> None:
        forbidden_geometry_calls = (
            "modeling.rounded_box(",
            "modeling.box_between(",
            "modeling.cylinder(",
            "modeling.boolean_apply(",
            "modeling.cut_batch(",
            "modeling.union_batch(",
            "bpy.ops.mesh.",
        )
        for project in VIEW_PROJECTS:
            text = (PROJECTS / project / "generate.py").read_text()
            with self.subTest(generator=project):
                self.assertIn("modeling.load_objects(", text)
                for call in forbidden_geometry_calls:
                    self.assertNotIn(call, text, call)

    def test_printable_generators_validate_what_they_produce(self) -> None:
        for project in PRINTABLE_PROJECTS:
            text = (PROJECTS / project / "generate.py").read_text()
            with self.subTest(generator=project):
                self.assertIn("validation.validate_fdm_part(", text)

    def test_legacy_layout_is_removed(self) -> None:
        self.assertFalse((CAD_ROOT / "blender").exists())
        self.assertFalse((REPOSITORY_ROOT / "tools" / "generate-cad").exists())
        for gone in (
            "single-tile",
            "single-tile-top",
            "single-tile-bottom",
            "single-tile-merged",
            "board-skeleton",
        ):
            self.assertFalse((PROJECTS / gone).exists(), gone)
        self.assertFalse((BLOCKS / "tile_electronics.py").exists())


class SharedModelingTest(unittest.TestCase):
    """The boolean traps that cost real debugging time stay documented."""

    def test_batch_helpers_warn_that_members_must_be_disjoint(self) -> None:
        text = (CAD_ROOT / "core" / "modeling.py").read_text()
        self.assertIn("def cut_batch(", text)
        self.assertIn("def union_batch(", text)
        self.assertIn("disjoint", text)

    def test_a_bevel_wider_than_its_box_is_refused(self) -> None:
        """It produces a silently invalid mesh rather than an error."""
        text = (CAD_ROOT / "core" / "modeling.py").read_text()
        self.assertIn("bevel radius", text)
        self.assertIn("min(dimensions)", text)

    def test_generators_use_the_shared_batch_helpers(self) -> None:
        for project in PRINTABLE_PROJECTS:
            text = (PROJECTS / project / "generate.py").read_text()
            with self.subTest(generator=project):
                self.assertIn("modeling.cut_batch(", text)
                self.assertNotIn("def _cut(", text)


class GeneratedLayoutTest(unittest.TestCase):
    """CAD and PCB agree on where build output lives."""

    def test_every_generator_writes_into_the_generated_folder(self) -> None:
        for generator in sorted(PROJECTS.glob("*/generate.py")):
            with self.subTest(generator=generator.parent.name):
                text = generator.read_text()
                self.assertIn('GENERATED = CAD_ROOT / "generated"', text)
                # Nothing may address the domain root directly for output.
                self.assertNotIn('CAD_ROOT / f"{NAME}', text)

    def test_the_main_directory_holds_no_artefacts(self) -> None:
        loose = {path.name for path in CAD_ROOT.iterdir() if path.is_file()}
        self.assertEqual(loose, {"README.md", "justfile"})
        self.assertTrue(GENERATED.is_dir())

    def test_the_domain_keeps_the_shared_directory_shape(self) -> None:
        """Both hardware domains present the same directories to a reader."""
        directories = {
            path.name
            for path in CAD_ROOT.iterdir()
            if path.is_dir() and path.name != "__pycache__"
        }
        self.assertEqual(
            directories,
            {"blocks", "core", "generated", "projects", "references", "tests"},
        )

    def test_generated_output_is_named_after_its_project(self) -> None:
        projects = {path.parent.name for path in PROJECTS.glob("*/generate.py")}
        artefacts = {path.name for path in GENERATED.iterdir()} - {"README.md"}
        self.assertTrue(artefacts)
        for artefact in artefacts:
            with self.subTest(artefact=artefact):
                self.assertTrue(
                    any(artefact.startswith(project) for project in projects),
                    artefact,
                )
        # Each project contributes at least its own model.
        for project in projects:
            self.assertIn(f"{project}.blend", artefacts, project)


if __name__ == "__main__":
    unittest.main()
