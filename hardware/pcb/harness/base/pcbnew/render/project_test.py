"""Exercise a real, small KiCad board project generated from harness declarations."""

import importlib.util
import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from typing import cast
from unittest.mock import patch

from pcb.harness.base.pcbnew.render.board_test import sample_board
from pcb.harness.examples.tiny_project import tiny_divider


@unittest.skipUnless(importlib.util.find_spec("pcbnew"), "KiCad Python module required")
class RenderProjectTest(unittest.TestCase):
    def test_generates_project_and_board_that_kicad_reopens(self) -> None:
        """The public builder yields matching project and native board files."""
        import pcbnew

        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "tiny-project"
            project = sample_board().write_project(target, "tiny")
            self.assertEqual(project, target / "tiny.kicad_pro")
            settings = cast(dict[str, object], json.loads(project.read_text()))
            meta = cast(dict[str, str], settings["meta"])
            self.assertEqual(meta["filename"], project.name)
            self.assertIn("board", settings)
            self.assertFalse((target / "tiny.kicad_prl").exists())
            board = pcbnew.LoadBoard(str(target / "tiny.kicad_pcb"))
            self.assertIsNotNone(board.FindFootprintByReference("U1"))

    def test_bad_name_cannot_create_a_project_directory(self) -> None:
        """A project name cannot escape or ambiguously name its output folder."""
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "project"
            with self.assertRaisesRegex(ValueError, "project name"):
                sample_board().write_project(target, "../outside")
            self.assertFalse(target.exists())

    def test_existing_directory_is_never_overwritten(self) -> None:
        """Re-running generation cannot silently replace a reviewed project."""
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "project"
            target.mkdir()
            with self.assertRaises(FileExistsError):
                sample_board().write_project(target, "tiny")

    def test_missing_parent_directories_are_created(self) -> None:
        """An author may choose a new nested output location directly."""
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "examples" / "tiny"
            project = sample_board().write_project(target, "tiny")
            self.assertTrue(project.is_file())

    def test_failed_native_save_removes_the_new_project(self) -> None:
        """A failed KiCad save cannot leave a partial project to review."""
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "tiny"
            with (
                patch(
                    "pcb.harness.base.pcbnew.render.project.pcbnew.SaveBoard",
                    return_value=False,
                ),
                self.assertRaisesRegex(OSError, "could not write"),
            ):
                sample_board().write_project(target, "tiny")
            self.assertFalse(target.exists())

    def test_repeated_generation_is_byte_for_byte_stable(self) -> None:
        """Regenerating an unchanged declaration should not create noisy diffs."""
        with tempfile.TemporaryDirectory() as directory:
            first = sample_board().write_project(Path(directory) / "first", "tiny")
            second = sample_board().write_project(Path(directory) / "second", "tiny")
            self.assertEqual(first.read_bytes(), second.read_bytes())
            self.assertEqual(
                first.with_suffix(".kicad_pcb").read_bytes(),
                second.with_suffix(".kicad_pcb").read_bytes(),
            )

    def test_two_footprint_project_is_byte_for_byte_stable(self) -> None:
        """Native collection order must not reorder distinct component blocks."""
        with tempfile.TemporaryDirectory() as directory:
            first = tiny_divider().write_project(Path(directory) / "first", "tiny")
            second = tiny_divider().write_project(Path(directory) / "second", "tiny")
            self.assertEqual(
                first.with_suffix(".kicad_pcb").read_bytes(),
                second.with_suffix(".kicad_pcb").read_bytes(),
            )

    @unittest.skipUnless(shutil.which("kicad-cli"), "KiCad CLI required")
    def test_tiny_project_passes_kicad_board_drc(self) -> None:
        """KiCad itself finds no rule violations in the generated tiny board."""
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "project"
            sample_board().write_project(target, "tiny")
            report = target / "drc.json"
            result = subprocess.run(
                (
                    "kicad-cli",
                    "pcb",
                    "drc",
                    "--severity-all",
                    "--format",
                    "json",
                    "-o",
                    str(report),
                    str(target / "tiny.kicad_pcb"),
                ),
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            findings = cast(dict[str, object], json.loads(report.read_text()))
            self.assertEqual(findings["violations"], [])
            # Unrouted pads appear in a separate DRC field, even when the
            # command exits successfully and reports no rule violations.
            self.assertEqual(findings["unconnected_items"], [])
