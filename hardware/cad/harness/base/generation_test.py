"""Blender errors cannot replace previously published CAD artifacts."""

import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock

from .generation import BlenderIdentity, blender_command, blender_identity, publish

RUNTIME = "4.5.13 LTS"
BUILD_HASH = "daeeeca98fb0"
IDENTITY: BlenderIdentity = {"version": RUNTIME, "build_hash": BUILD_HASH}


def selected_identity(_: Path) -> BlenderIdentity:
    return IDENTITY


class GenerationTest(unittest.TestCase):
    def test_private_xvfb_is_used_even_with_a_forwarded_display(self) -> None:
        command = blender_command(
            Path("blender"),
            Path("generate.py"),
            Path("stage"),
            find_executable=lambda _: "/usr/bin/xvfb-run",
        )
        self.assertEqual(command[:2], ["xvfb-run", "--auto-servernum"])
        self.assertIn("--python-exit-code", command)
        self.assertEqual(command[-2:], ["--", "stage"])

    def test_missing_xvfb_uses_blender_directly(self) -> None:
        command = blender_command(
            Path("blender"),
            Path("generate.py"),
            Path("stage"),
            find_executable=lambda _: None,
        )
        self.assertEqual(command[0], "blender")

    def test_blender_identity_reads_the_selected_executable(self) -> None:
        def version(
            command: list[str], **options: object
        ) -> subprocess.CompletedProcess[str]:
            self.assertEqual(command, ["/opt/blender/blender", "--version"])
            self.assertTrue(options["check"])
            self.assertTrue(options["capture_output"])
            self.assertTrue(options["text"])
            return subprocess.CompletedProcess(
                command,
                0,
                f"Blender {RUNTIME}\n\tbuild hash: {BUILD_HASH}\n",
                "",
            )

        self.assertEqual(
            blender_identity(Path("/opt/blender/blender"), runner=version), IDENTITY
        )

    def test_unrecognised_blender_version_is_rejected(self) -> None:
        def invalid(
            command: list[str], **options: object
        ) -> subprocess.CompletedProcess[str]:
            return subprocess.CompletedProcess(command, 0, "unexpected output\n", "")

        with self.assertRaisesRegex(RuntimeError, "version"):
            blender_identity(Path("blender"), runner=invalid)

    def test_blender_identity_requires_a_build_hash(self) -> None:
        def missing_hash(
            command: list[str], **options: object
        ) -> subprocess.CompletedProcess[str]:
            return subprocess.CompletedProcess(command, 0, f"Blender {RUNTIME}\n", "")

        with self.assertRaisesRegex(RuntimeError, "build hash"):
            blender_identity(Path("blender"), runner=missing_hash)

    def test_failure_preserves_previous_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "generated"
            output.mkdir()
            (output / "reviewed.blend").write_text("old")

            def fail(command: list[str], **options: object) -> None:
                raise subprocess.CalledProcessError(1, command)

            with self.assertRaises(subprocess.CalledProcessError):
                publish(
                    Path("blender"),
                    Path("generate.py"),
                    output,
                    runner=fail,
                    identity_reader=selected_identity,
                )
            self.assertEqual((output / "reviewed.blend").read_text(), "old")

    def test_prepare_failure_happens_before_the_blender_version_probe(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "generated"
            read_identity = Mock(return_value=IDENTITY)

            def fail_prepare(stage: Path) -> None:
                raise RuntimeError("dependency failed")

            with self.assertRaisesRegex(RuntimeError, "dependency failed"):
                publish(
                    Path("missing-blender"),
                    Path("generate.py"),
                    output,
                    prepare=fail_prepare,
                    identity_reader=read_identity,
                )
            read_identity.assert_not_called()

    def test_incomplete_success_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "generated"

            def incomplete(command: list[str], **options: object) -> None:
                (Path(command[-1]) / "case.blend").write_text("not complete")

            with self.assertRaisesRegex(RuntimeError, "manifest"):
                publish(
                    Path("blender"),
                    Path("generate.py"),
                    output,
                    runner=incomplete,
                    identity_reader=selected_identity,
                )
            self.assertFalse(output.exists())

    def test_complete_generation_replaces_previous_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "generated"
            output.mkdir()
            (output / "obsolete.blend").write_text("old")

            def complete(command: list[str], **options: object) -> None:
                stage = Path(command[-1])
                self.assertEqual((stage / "source.json").read_text(), "fresh")
                (stage / "case.blend").write_text("new")
                from .provenance import record_provenance

                manifest: dict[str, object] = {
                    "checks_passed": True,
                    "blender_runtime": IDENTITY,
                    "outputs": ["case.blend"],
                }
                record_provenance(stage, manifest)
                (stage / "manifest.json").write_text(json.dumps(manifest))

            def prepare(stage: Path) -> None:
                (stage / "source.json").write_text("fresh")

            publish(
                Path("blender"),
                Path("generate.py"),
                output,
                runner=complete,
                prepare=prepare,
                identity_reader=selected_identity,
            )
            self.assertEqual((output / "case.blend").read_text(), "new")
            self.assertFalse((output / "obsolete.blend").exists())

    def test_missing_declared_output_preserves_previous_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "generated"
            output.mkdir()
            (output / "reviewed.blend").write_text("old")

            def incomplete(command: list[str], **options: object) -> None:
                (Path(command[-1]) / "manifest.json").write_text(
                    json.dumps(
                        {
                            "checks_passed": True,
                            "blender_runtime": IDENTITY,
                            "outputs": ["missing.png"],
                        }
                    )
                )

            with self.assertRaisesRegex(RuntimeError, "missing output"):
                publish(
                    Path("blender"),
                    Path("generate.py"),
                    output,
                    runner=incomplete,
                    identity_reader=selected_identity,
                )
            self.assertEqual((output / "reviewed.blend").read_text(), "old")

    def test_tampered_artifact_is_rejected_before_publication(self) -> None:
        from .provenance import artifacts_current, record_provenance

        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "generated"

            def tampered(command: list[str], **options: object) -> None:
                stage = Path(command[-1])
                (stage / "case.blend").write_text("checked geometry")
                manifest: dict[str, object] = {
                    "checks_passed": True,
                    "blender_runtime": IDENTITY,
                    "outputs": ["case.blend"],
                }
                record_provenance(stage, manifest)
                (stage / "manifest.json").write_text(json.dumps(manifest))
                self.assertTrue(artifacts_current(stage))
                (stage / "case.blend").write_text("altered geometry")

            with self.assertRaisesRegex(RuntimeError, "provenance"):
                publish(
                    Path("blender"),
                    Path("generate.py"),
                    output,
                    runner=tampered,
                    identity_reader=selected_identity,
                )
            self.assertFalse(output.exists())

    def test_sources_changed_during_worker_are_rejected(self) -> None:
        from unittest.mock import patch

        from .provenance import record_provenance

        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "generated"
            output.mkdir()
            (output / "reviewed.blend").write_text("old")

            def complete(command: list[str], **options: object) -> None:
                stage = Path(command[-1])
                (stage / "case.blend").write_text("new")
                manifest: dict[str, object] = {
                    "checks_passed": True,
                    "blender_runtime": IDENTITY,
                    "outputs": ["case.blend"],
                }
                record_provenance(stage, manifest)
                (stage / "manifest.json").write_text(json.dumps(manifest))

            with (
                patch(
                    "cad.harness.base.generation.source_digest",
                    return_value="before worker loaded code",
                ),
                self.assertRaisesRegex(RuntimeError, "provenance"),
            ):
                publish(
                    Path("blender"),
                    Path("generate.py"),
                    output,
                    runner=complete,
                    identity_reader=selected_identity,
                )
            self.assertEqual((output / "reviewed.blend").read_text(), "old")

    def test_worker_runtime_must_match_the_selected_blender(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "generated"

            def mismatched(command: list[str], **options: object) -> None:
                stage = Path(command[-1])
                (stage / "case.blend").write_text("new")
                from .provenance import record_provenance

                manifest: dict[str, object] = {
                    "checks_passed": True,
                    "blender_runtime": {
                        "version": RUNTIME,
                        "build_hash": "different-build",
                    },
                    "outputs": ["case.blend"],
                }
                record_provenance(stage, manifest)
                (stage / "manifest.json").write_text(json.dumps(manifest))

            with self.assertRaisesRegex(RuntimeError, "runtime"):
                publish(
                    Path("blender"),
                    Path("generate.py"),
                    output,
                    runner=mismatched,
                    identity_reader=selected_identity,
                )
            self.assertFalse(output.exists())

    def test_worker_runtime_identity_must_include_the_build_hash(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "generated"

            def missing_identity(command: list[str], **options: object) -> None:
                stage = Path(command[-1])
                (stage / "case.blend").write_text("new")
                from .provenance import record_provenance

                manifest: dict[str, object] = {
                    "checks_passed": True,
                    "blender_runtime": {"version": RUNTIME},
                    "outputs": ["case.blend"],
                }
                record_provenance(stage, manifest)
                (stage / "manifest.json").write_text(json.dumps(manifest))

            with self.assertRaisesRegex(RuntimeError, "runtime"):
                publish(
                    Path("blender"),
                    Path("generate.py"),
                    output,
                    runner=missing_identity,
                    identity_reader=selected_identity,
                )
            self.assertFalse(output.exists())
