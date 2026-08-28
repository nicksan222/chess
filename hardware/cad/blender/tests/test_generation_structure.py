"""Tests for CAD generator ownership, reuse, and main-runner ordering."""

from pathlib import Path
import subprocess
import unittest


REPOSITORY_ROOT = Path(__file__).resolve().parents[4]
BLENDER_ROOT = REPOSITORY_ROOT / "hardware" / "cad" / "blender"


class GeneratorStructureTest(unittest.TestCase):
    def test_main_runner_discovers_every_project_in_dependency_order(self) -> None:
        result = subprocess.run(
            ["./tools/generate-cad", "--list"],
            cwd=REPOSITORY_ROOT,
            check=True,
            text=True,
            capture_output=True,
        )
        discovered = [
            line.split("\t", 1)[1] for line in result.stdout.splitlines()
        ]
        self.assertEqual(
            discovered,
            [
                "hardware/cad/blender/single-tile/top/generate.py",
                "hardware/cad/blender/single-tile/bottom/generate.py",
                "hardware/cad/blender/single-tile/merged/generate.py",
                "hardware/cad/blender/board-skeleton/generate.py",
                "hardware/cad/blender/board-assembly/generate.py",
            ],
        )

    def test_every_printable_model_has_one_owning_generator(self) -> None:
        ownership = {
            "Tile_Top_Lid": BLENDER_ROOT / "single-tile" / "top" / "generate.py",
            "Tile_Bottom_Tray": BLENDER_ROOT
            / "single-tile"
            / "bottom"
            / "generate.py",
            "Printable_Empty_Board_Tray": BLENDER_ROOT
            / "board-skeleton"
            / "generate.py",
        }
        generator_text = {
            path: path.read_text() for path in set(ownership.values())
        }
        for object_name, owner in ownership.items():
            with self.subTest(object_name=object_name):
                self.assertIn(f'"{object_name}"', generator_text[owner])
                other_text = "\n".join(
                    text for path, text in generator_text.items() if path != owner
                )
                self.assertNotIn(f'"{object_name}"', other_text)

    def test_views_import_printable_sources_without_redefining_them(self) -> None:
        view_generators = (
            BLENDER_ROOT / "single-tile" / "merged" / "generate.py",
            BLENDER_ROOT / "board-assembly" / "generate.py",
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

    def test_legacy_monolithic_single_tile_generator_is_removed(self) -> None:
        self.assertFalse((BLENDER_ROOT / "single-tile" / "generate.py").exists())
        self.assertFalse(
            (BLENDER_ROOT / "single-tile" / "single-tile.blend").exists()
        )


if __name__ == "__main__":
    unittest.main()
