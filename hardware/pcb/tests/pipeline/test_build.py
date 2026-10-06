"""Failure isolation and release gating of the single build pipeline.

These tests use temporary directories and mock out the expensive steps (KiCad,
routing, SPICE), so they check the pipeline's *control flow* guarantees, not the
design: failures never damage published output, publication is all-or-nothing,
and `release` cannot export fabrication files without the physical evidence.
"""

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from build_support import staged_output

from pcb import build


class BuildTest(unittest.TestCase):
    def test_failed_generation_never_changes_published_files(self):
        # Simulate a generator crashing half way: the previously published set
        # must be untouched and the partial staging output must not appear.
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
        # Publication swaps the whole directory, so a report that the new build no
        # longer produces cannot linger and be mistaken for current evidence.
        with tempfile.TemporaryDirectory() as directory:
            out = Path(directory) / "generated"
            out.mkdir()
            (out / "stale-drc.json").write_text("old")
            with build.staged_output(out) as stage:
                (stage / "new").write_text("complete")
            self.assertEqual([p.name for p in out.iterdir()], ["new"])

    def test_pcb_build_keeps_staged_output_import_compatibility(self):
        # `build.staged_output` must remain the shared helper, not a local copy.
        self.assertIs(build.staged_output, staged_output)

    def test_source_hashes_cover_publication_helper_contents(self):
        # The publication helper is part of the build, so editing it must change
        # the recorded source hashes (and trip the mid-build change guard).
        helper = build.PCB_ROOT.parent / "build_support.py"
        key = str(helper.relative_to(build.REPOSITORY_ROOT))
        before = build.source_hashes()
        original_read = type(helper).read_bytes

        # Pretend the helper's bytes changed, without touching the real file.
        def changed_contents(path: Path) -> bytes:
            contents = original_read(path)
            return (
                contents + b"\n# simulated source change\n"
                if path == helper
                else contents
            )

        with patch.object(
            type(helper), "read_bytes", autospec=True, side_effect=changed_contents
        ):
            after = build.source_hashes()

        self.assertIn(key, before)
        self.assertNotEqual(before[key], after[key])

    def test_release_cannot_export_or_publish_when_evidence_gate_fails(self):
        # Every other step succeeds (mocked); only the evidence gate fails. Expect
        # no fabrication export, no previews, and the old output left in place.
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

    def test_release_runs_both_gates_and_reports_both_reasons(self):
        # Evidence and verification gates both run; one refusal lists both reasons.
        with tempfile.TemporaryDirectory() as directory:
            out = Path(directory) / "generated"
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
                patch.object(
                    build,
                    "verification_gate",
                    side_effect=RuntimeError("open verification items"),
                ) as gate,
                patch.object(build, "tests"),
                patch.object(build, "fabrication") as fabrication,
                patch.object(build, "previews"),
            ):
                with self.assertRaises(RuntimeError) as raised:
                    build.build("release", out)
                gate.assert_called_once_with()
                fabrication.assert_not_called()
            self.assertIn("missing physical evidence", str(raised.exception))
            self.assertIn("open verification items", str(raised.exception))

    def test_source_change_during_build_refuses_publication(self):
        # The two `source_hashes` calls (before/after the build) disagree, as if a
        # file was edited mid-build: nothing may be published.
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
        # The mocked tool "succeeds", but the DRC report lists an unconnected item.
        # The build must read the reports and fail rather than trust exit status.
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
