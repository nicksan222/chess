"""Failure isolation and dependency handling for CAD publication."""

import subprocess
import tempfile
import unittest
from pathlib import Path

from cad import build


class CadBuildTest(unittest.TestCase):
    def _runner(self, *, fail_on: str | None = None):
        calls: list[str] = []

        def run(command: list[str], **_options: object) -> None:
            generator = Path(command[command.index("--python") + 1]).parent.name
            output = Path(command[-1])
            calls.append(generator)
            if generator == fail_on:
                raise subprocess.CalledProcessError(1, command)
            if generator == "board-case":
                (output / "board-case.blend").write_text("case")
                (output / "board-case.png").write_text("case render")
            elif generator == "tile-plate":
                (output / "tile-plate.blend").write_text("plate")
                (output / "tile-plate.png").write_text("plate render")
            elif generator == "board-assembly":
                self.assertTrue((output / "board-case.blend").is_file())
                self.assertTrue((output / "tile-plate.blend").is_file())
                (output / "board-assembly.blend").write_text("assembly")

        return calls, run

    def test_headless_command_keeps_xvfb_and_one_output_directory(self) -> None:
        command = build.generator_command(
            Path("blender"),
            Path("project/generate.py"),
            Path("stage"),
            environment={},
            find_executable=lambda name: f"/usr/bin/{name}",
        )
        self.assertEqual(command[:2], ["xvfb-run", "--auto-servernum"])
        self.assertEqual(command[-2:], ["--", "stage"])

    def test_empty_generation_order_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory) / "example"
            project.mkdir()
            (project / "generate.py").write_text("")
            (project / "generation-order").write_text("")
            with self.assertRaisesRegex(RuntimeError, "Invalid generation order"):
                build.ordered_generators(Path(directory))

    def test_clean_first_run_builds_dependencies_in_one_stage(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "generated"
            calls, runner = self._runner()
            build.generate(Path("blender"), output, runner)
            self.assertEqual(calls, ["board-case", "tile-plate", "board-assembly"])
            self.assertTrue((output / "board-assembly.blend").is_file())
            self.assertTrue((output / "README.md").is_file())

    def test_success_replaces_the_whole_set(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "generated"
            output.mkdir()
            (output / "obsolete.blend").write_text("old")
            _calls, runner = self._runner()
            build.generate(Path("blender"), output, runner)
            self.assertFalse((output / "obsolete.blend").exists())
            self.assertTrue((output / "board-case.blend").is_file())

    def test_generator_failure_preserves_previous_output(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "generated"
            output.mkdir()
            (output / "reviewed.blend").write_text("old")
            _calls, runner = self._runner(fail_on="tile-plate")
            with self.assertRaises(subprocess.CalledProcessError):
                build.generate(Path("blender"), output, runner)
            self.assertEqual(
                {path.name for path in output.iterdir()}, {"reviewed.blend"}
            )


if __name__ == "__main__":
    unittest.main()
