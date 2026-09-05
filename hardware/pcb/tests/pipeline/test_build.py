"""Failure isolation and release gating of the single build pipeline."""

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from pcb import build


class BuildTest(unittest.TestCase):
    def test_failed_generation_never_changes_published_files(self):
        with tempfile.TemporaryDirectory() as directory:
            out = Path(directory) / "generated"
            out.mkdir()
            (out / "old").write_text("reviewed")
            with (
                self.assertRaisesRegex(RuntimeError, "broken"),
                build.staged_output(out) as stage,
            ):
                (stage / "new").write_text("partial")
                raise RuntimeError("broken generator")
            self.assertEqual([p.name for p in out.iterdir()], ["old"])
            self.assertEqual((out / "old").read_text(), "reviewed")

    def test_publication_replaces_whole_set_including_obsolete_reports(self):
        with tempfile.TemporaryDirectory() as directory:
            out = Path(directory) / "generated"
            out.mkdir()
            (out / "stale-drc.json").write_text("old")
            with build.staged_output(out) as stage:
                (stage / "new").write_text("complete")
            self.assertEqual([p.name for p in out.iterdir()], ["new"])

    def test_release_cannot_export_or_publish_when_evidence_gate_fails(self):
        with tempfile.TemporaryDirectory() as directory:
            out = Path(directory) / "generated"
            out.mkdir()
            (out / "reviewed").write_text("old")
            with (
                patch.object(build, "check"),
                patch.object(build, "doctor", return_value={}),
                patch.object(build, "generate"),
                patch.object(build, "native_checks"),
                patch.object(
                    build,
                    "physical_evidence",
                    side_effect=RuntimeError("missing physical evidence"),
                ),
                patch.object(build, "tests"),
                patch.object(build, "fabrication") as fabrication,
                patch.object(build, "previews") as previews,
            ):
                with self.assertRaisesRegex(RuntimeError, "missing physical evidence"):
                    build.build("release", out)
                fabrication.assert_not_called()
                previews.assert_not_called()
            self.assertEqual([p.name for p in out.iterdir()], ["reviewed"])

    def test_source_change_during_build_refuses_publication(self):
        with tempfile.TemporaryDirectory() as directory:
            out = Path(directory) / "generated"
            with (
                patch.object(build, "doctor", return_value={}),
                patch.object(build, "generate"),
                patch.object(
                    build,
                    "source_hashes",
                    side_effect=[{"a": "before"}, {"a": "after"}],
                ),
                self.assertRaisesRegex(RuntimeError, "source changed"),
            ):
                build.build("generate", out)
            self.assertFalse(out.exists())

    def test_native_zero_exit_is_not_enough_when_report_has_violations(self):
        with tempfile.TemporaryDirectory() as directory:
            out = Path(directory)
            (out / "erc.json").write_text(json.dumps({"sheets": [{"violations": []}]}))
            (out / "drc.json").write_text(
                json.dumps(
                    {
                        "violations": [],
                        "schematic_parity": [],
                        "unconnected_items": [{}],
                    }
                )
            )
            with (
                patch.object(build, "run"),
                self.assertRaisesRegex(RuntimeError, "checks failed"),
            ):
                build.native_checks(out)
