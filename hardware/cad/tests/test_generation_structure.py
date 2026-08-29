"""Tests for CAD generator ownership, reuse, and main-runner ordering."""

from pathlib import Path
import subprocess
import unittest


REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
CAD_ROOT = REPOSITORY_ROOT / "hardware" / "cad"
PROJECTS = CAD_ROOT / "projects"
GENERATED = CAD_ROOT / "generated"


class GeneratorStructureTest(unittest.TestCase):
    def test_main_runner_discovers_every_project_in_dependency_order(self) -> None:
        result = subprocess.run(
            ["./tools/cad", "list"],
            cwd=REPOSITORY_ROOT,
            check=True,
            text=True,
            capture_output=True,
        )
        self.assertEqual(
            result.stdout.splitlines(),
            [
                "hardware/cad/projects/single-tile-top/generate.py",
                "hardware/cad/projects/single-tile-bottom/generate.py",
                "hardware/cad/projects/single-tile-merged/generate.py",
                "hardware/cad/projects/board-skeleton/generate.py",
                "hardware/cad/projects/board-assembly/generate.py",
            ],
        )

    def test_every_printable_model_has_one_owning_generator(self) -> None:
        ownership = {
            "Tile_Top_Lid": PROJECTS / "single-tile-top" / "generate.py",
            "Tile_Bottom_Tray": PROJECTS / "single-tile-bottom" / "generate.py",
            "Printable_Empty_Board_Tray": PROJECTS / "board-skeleton" / "generate.py",
        }
        generator_text = {path: path.read_text() for path in set(ownership.values())}
        for object_name, owner in ownership.items():
            with self.subTest(object_name=object_name):
                self.assertIn(f'"{object_name}"', generator_text[owner])
                other_text = "\n".join(
                    text for path, text in generator_text.items() if path != owner
                )
                self.assertNotIn(f'"{object_name}"', other_text)

    def test_views_import_printable_sources_without_redefining_them(self) -> None:
        view_generators = (
            PROJECTS / "single-tile-merged" / "generate.py",
            PROJECTS / "board-assembly" / "generate.py",
        )
        forbidden_geometry_calls = (
            "modeling.rounded_box(",
            "modeling.cylinder(",
            "modeling.boolean_apply(",
            "bpy.ops.mesh.",
        )
        for generator in view_generators:
            text = generator.read_text()
            with self.subTest(generator=generator):
                self.assertIn("modeling.load_objects(", text)
                for call in forbidden_geometry_calls:
                    self.assertNotIn(call, text)

    def test_legacy_layout_is_removed(self) -> None:
        self.assertFalse((CAD_ROOT / "blender").exists())
        self.assertFalse((PROJECTS / "single-tile").exists())
        self.assertFalse((REPOSITORY_ROOT / "tools" / "generate-cad").exists())


class GeneratedLayoutTest(unittest.TestCase):
    """CAD and electronics agree on where build output lives."""

    def test_every_generator_writes_into_the_generated_folder(self) -> None:
        for generator in sorted(PROJECTS.glob("*/generate.py")):
            with self.subTest(generator=generator.parent.name):
                text = generator.read_text()
                self.assertIn('GENERATED = CAD_ROOT / "generated"', text)
                # Nothing may address the domain root directly for output.
                self.assertNotIn('CAD_ROOT / f"{NAME}', text)

    def test_the_main_directory_holds_no_artefacts(self) -> None:
        loose = {path.name for path in CAD_ROOT.iterdir() if path.is_file()}
        self.assertEqual(loose, {"README.md"})
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
