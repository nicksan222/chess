"""Reject mismatched source, altered exports, and missing PCB geometry."""

import json
import shutil
import tempfile
import unittest
from functools import partial
from pathlib import Path
from unittest.mock import patch

from cad.harness.base.pcb import PcbSnapshot
from cad.harness.base.pcb_export import (
    export_current,
    pcb_bundle_current,
    prepare_export,
)
from pcb.harness.base.pcbnew.model_export import file_digest
from pcb.harness.base.pcbnew.model_export_test import glb


class PcbExportTest(unittest.TestCase):
    def write_export(self, root: Path, snapshot: PcbSnapshot) -> dict[str, str]:
        glb(
            root / "chess-board.glb",
            [
                {"name": part.reference, "mesh": index}
                for index, part in enumerate(snapshot.parts)
            ],
        )
        snapshot.write(root / "pcb-components.json")
        (root / "chess-board.kicad_pcb").write_text("fixture PCB")
        report = {
            "source_digest": "current",
            "snapshot_sha256": file_digest(root / "pcb-components.json"),
            "pcb_sha256": file_digest(root / "chess-board.kicad_pcb"),
            "glb_sha256": file_digest(root / "chess-board.glb"),
        }
        (root / "3d-models.json").write_text(json.dumps(report))
        return report

    def test_reviewed_export_is_reused_without_regenerating_pcb(self) -> None:
        snapshot = PcbSnapshot.current()
        with tempfile.TemporaryDirectory() as directory:
            source, stage = Path(directory) / "source", Path(directory) / "stage"
            source.mkdir()
            stage.mkdir()
            self.write_export(source, snapshot)
            with (
                patch("cad.harness.base.pcb_export.SOURCE", source),
                patch(
                    "cad.harness.base.pcb_export.source_digest", return_value="current"
                ),
                patch("pcb.board.generate.generate") as generate,
            ):
                prepare_export(stage)
                generate.assert_not_called()
                self.assertTrue(pcb_bundle_current(stage, snapshot))
            self.assertEqual(
                (source / "chess-board.glb").read_bytes(),
                (stage / "chess-board.glb").read_bytes(),
            )

    def test_missing_stale_or_damaged_export_is_refreshed_before_copy(self) -> None:
        snapshot = PcbSnapshot.current()
        for invalid in ("missing", "stale", "damaged"):
            with (
                self.subTest(invalid=invalid),
                tempfile.TemporaryDirectory() as directory,
            ):
                source, stage = Path(directory) / "source", Path(directory) / "stage"
                source.mkdir()
                stage.mkdir()
                if invalid != "missing":
                    self.write_export(source, snapshot)
                    if invalid == "stale":
                        report = source / "3d-models.json"
                        report.write_text(report.read_text().replace("current", "old"))
                    else:
                        (source / "chess-board.glb").write_bytes(b"damaged model")
                with (
                    patch("cad.harness.base.pcb_export.SOURCE", source),
                    patch(
                        "cad.harness.base.pcb_export.source_digest",
                        return_value="current",
                    ),
                    patch(
                        "pcb.board.generate.generate",
                        side_effect=partial(self.write_export, source, snapshot),
                    ) as generate,
                ):
                    self.assertFalse(export_current(source))
                    prepare_export(stage)
                    generate.assert_called_once_with()
                    self.assertTrue(pcb_bundle_current(stage, snapshot))

    def test_pcb_failure_stops_blender_and_preserves_previous_cad(self) -> None:
        from cad.board.generate import generate

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            output = root / "cad"
            output.mkdir()
            (output / "reviewed.blend").write_text("previous CAD")
            with (
                patch("cad.harness.base.pcb_export.SOURCE", root / "missing-pcb"),
                patch(
                    "pcb.board.generate.generate",
                    side_effect=RuntimeError("PCB checks failed"),
                ),
                patch("cad.harness.base.generation.blender_command") as blender,
                self.assertRaisesRegex(RuntimeError, "PCB checks failed"),
            ):
                generate(Path("blender"), output)
            blender.assert_not_called()
            self.assertEqual(
                [path.name for path in output.iterdir()], ["reviewed.blend"]
            )
            self.assertEqual((output / "reviewed.blend").read_text(), "previous CAD")

    def test_export_must_match_source_and_both_artifacts(self) -> None:
        snapshot = PcbSnapshot.current()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.write_export(root, snapshot)
            with patch(
                "cad.harness.base.pcb_export.source_digest", return_value="current"
            ):
                self.assertTrue(export_current(root, snapshot))
                self.assertTrue(pcb_bundle_current(root, snapshot))
                (root / "chess-board.kicad_pcb").write_text("changed PCB")
                self.assertFalse(export_current(root, snapshot))
                self.assertTrue(pcb_bundle_current(root, snapshot))
            with patch(
                "cad.harness.base.pcb_export.source_digest", return_value="changed"
            ):
                self.assertFalse(pcb_bundle_current(root, snapshot))
                self.assertFalse(export_current(root, snapshot))
            (root / "chess-board.glb").unlink()
            self.assertFalse(export_current(root, snapshot))

    def test_mixed_copy_is_retried_and_metadata_is_not_rebuilt(self) -> None:
        snapshot = PcbSnapshot.current()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source, stage = root / "source", root / "stage"
            source.mkdir()
            stage.mkdir()
            report = self.write_export(source, snapshot)
            copy = shutil.copyfile
            corrupted = False

            def racing_copy(src: Path, dest: Path) -> Path:
                nonlocal corrupted
                result = copy(src, dest)
                if dest.name == "chess-board.glb" and not corrupted:
                    dest.write_bytes(b"mixed publication")
                    corrupted = True
                return result

            with (
                patch("cad.harness.base.pcb_export.SOURCE", source),
                patch(
                    "cad.harness.base.pcb_export.source_digest", return_value="current"
                ),
                patch(
                    "cad.harness.base.pcb_export.shutil.copyfile",
                    side_effect=racing_copy,
                ),
            ):
                prepare_export(stage, snapshot)
            self.assertEqual(
                file_digest(stage / "chess-board.glb"), report["glb_sha256"]
            )
            self.assertEqual(PcbSnapshot.read(stage / "pcb-components.json"), snapshot)

    def test_cad_bundle_rechecks_pcb_source_and_report_binding(self) -> None:
        from cad.harness.base.provenance import artifacts_current, record_provenance

        snapshot = PcbSnapshot.current()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            report = self.write_export(root, snapshot)
            (root / "chess-board.kicad_pcb").unlink()
            manifest: dict[str, object] = {
                "checks_passed": True,
                "outputs": ["chess-board.glb", "pcb-components.json", "3d-models.json"],
            }
            record_provenance(root, manifest)
            (root / "manifest.json").write_text(json.dumps(manifest))
            with patch(
                "cad.harness.base.pcb_export.source_digest", return_value="current"
            ):
                self.assertTrue(artifacts_current(root))
                manifest["pcb_provenance"] = {**report, "pcb_sha256": "wrong-board"}
                (root / "manifest.json").write_text(json.dumps(manifest))
                self.assertFalse(artifacts_current(root))
            record_provenance(root, manifest)
            (root / "manifest.json").write_text(json.dumps(manifest))
            with patch(
                "cad.harness.base.pcb_export.source_digest",
                return_value="edited-during-render",
            ):
                self.assertFalse(artifacts_current(root))
