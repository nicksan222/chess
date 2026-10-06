"""End-to-end tests for a small, reviewable circuit using both renderers."""

import importlib.util
import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from typing import cast

from pcb.harness.examples.tiny_project import TinyNet, tiny_divider


class TinyProjectTest(unittest.TestCase):
    def test_one_declaration_describes_parts_route_and_spice_check(self) -> None:
        """The example exposes all three intents without native SDK objects."""
        board = tiny_divider()
        self.assertEqual(
            tuple(part.reference for part in board.components()), ("R1", "R2")
        )
        self.assertEqual(len(board.traces()), 1)
        self.assertIs(board.traces()[0].net, TinyNet.MID)
        deck = board.deck("nominal")
        self.assertIn("R1", deck)
        self.assertIn("R2", deck)
        self.assertIn("result_r2_0", deck)

    @unittest.skipUnless(shutil.which("ngspice"), "ngspice required")
    def test_nominal_midpoint_is_proved_by_ngspice(self) -> None:
        """The actual simulator reports about half of the 3.3 V supply."""
        result = tiny_divider().run("nominal")
        self.assertAlmostEqual(result["result_r2_0"], 1.65, places=3)

    @unittest.skipUnless(
        importlib.util.find_spec("pcbnew") and shutil.which("kicad-cli"),
        "KiCad Python and CLI required",
    )
    def test_generated_project_passes_real_kicad_drc(self) -> None:
        """The same declaration saves a board with no KiCad DRC violations."""
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "tiny-divider"
            project = tiny_divider().write_project(root, "tiny-divider")
            self.assertTrue(project.is_file())
            report = root / "drc.json"
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
                    str(root / "tiny-divider.kicad_pcb"),
                ),
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            findings = cast(dict[str, object], json.loads(report.read_text()))
            self.assertEqual(findings["violations"], [])
            # KiCad reports missing copper connections separately from rule
            # violations; both must be empty for this example to pass.
            self.assertEqual(findings["unconnected_items"], [])

    @unittest.skipUnless(
        importlib.util.find_spec("pcbnew") and shutil.which("kicad-cli"),
        "KiCad Python and CLI required",
    )
    def test_drc_reports_a_missing_midpoint_track_as_unconnected(self) -> None:
        """A zero exit code and no violations alone cannot prove routing."""
        import pcbnew

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "tiny-divider"
            tiny_divider().write_project(root, "tiny-divider")
            board_path = root / "tiny-divider.kicad_pcb"
            native = pcbnew.LoadBoard(str(board_path))
            tracks = list(native.GetTracks())
            self.assertEqual(len(tracks), 1)
            native.Remove(tracks[0])
            pcbnew.SaveBoard(str(board_path), native)
            report = root / "unrouted-drc.json"
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
                    str(board_path),
                ),
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            findings = cast(dict[str, object], json.loads(report.read_text()))
            self.assertEqual(findings["violations"], [])
            self.assertNotEqual(findings["unconnected_items"], [])
