"""A moved KiCad project must still export its attached component models."""

import importlib.util
import json
import shutil
import subprocess
import tempfile
import unittest
from contextlib import ExitStack
from pathlib import Path
from types import SimpleNamespace
from typing import cast
from unittest.mock import patch

from pcb.board.assembly import PcbSnapshot
from pcb.harness.base.circuit import Circuit
from pcb.harness.base.net import Net
from pcb.harness.base.pcbnew.render.board_test import sample_board


class RecordExportTest(unittest.TestCase):
    def test_record_export_stamps_the_digest_captured_before_generation(self) -> None:
        from .models import record_export

        product = SimpleNamespace(key="TEST", body_mm=(1.0, 1.0, 1.0))
        definition = SimpleNamespace(product=product, model_3d=None)
        part = SimpleNamespace(reference="U1", definition=definition)
        circuit = SimpleNamespace(components=lambda: (part,))

        def write_snapshot(path: Path) -> None:
            path.write_text("{}\n")

        snapshot = SimpleNamespace(write=write_snapshot)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            board_path = root / "fixture.kicad_pcb"
            glb_path = root / "fixture.glb"
            board_path.write_bytes(b"board")
            glb_path.write_bytes(b"model")
            with (
                patch("pcb.harness.base.pcbnew.model_export.check_component_coverage"),
                patch(
                    "pcb.harness.base.pcbnew.model_export.source_digest",
                    side_effect=AssertionError("source digest must not be recaptured"),
                ),
            ):
                record_export(
                    cast(Circuit[Net], cast(object, circuit)),
                    board_path,
                    glb_path,
                    cast(PcbSnapshot, cast(object, snapshot)),
                    "captured-source",
                )
            report = cast(
                dict[str, object],
                json.loads((root / "3d-models.json").read_text()),
            )
            self.assertEqual(report["source_digest"], "captured-source")

    def test_generation_refuses_publication_if_sources_change(self) -> None:
        from pcb.board import generate

        board = SimpleNamespace(
            route=lambda: None, design_rules=None, fabrication_pending=True
        )
        snapshot = SimpleNamespace()
        source_state = "captured-source"

        def build_board() -> SimpleNamespace:
            nonlocal source_state
            source_state = "changed-source"
            return board

        patched_functions = (
            "run",
            "write_schematic_project",
            "write_bom",
            "apply_netlist",
            "write_rules",
            "fill_planes",
            "attach_models",
            "write_connections",
            "check_schematic_parity",
            "check_routed_copper",
            "prepare_svg",
            "record_export",
            "write_assembly",
            "write_fabrication",
            "write_report",
        )
        with tempfile.TemporaryDirectory() as directory, ExitStack() as stack:
            output = Path(directory) / "generated"
            output.mkdir()
            (output / "old").write_text("reviewed")
            for name in patched_functions:
                stack.enter_context(patch.object(generate, name))
            stack.enter_context(
                patch.object(generate, "Board", side_effect=build_board)
            )
            stack.enter_context(
                patch.object(generate, "run_suite", return_value={"complete": True})
            )
            stack.enter_context(
                patch.object(PcbSnapshot, "from_board", return_value=snapshot)
            )
            stack.enter_context(
                patch.object(
                    generate,
                    "source_digest",
                    side_effect=lambda: source_state,
                )
            )
            with self.assertRaisesRegex(RuntimeError, "source changed"):
                generate.generate(output)
            self.assertEqual((output / "old").read_text(), "reviewed")


@unittest.skipUnless(
    importlib.util.find_spec("pcbnew")
    and importlib.util.find_spec("cadquery")
    and shutil.which("kicad-cli"),
    "KiCad and CadQuery required",
)
class ModelsTest(unittest.TestCase):
    def test_portable_step_attachment_survives_project_relocation(self) -> None:
        import pcbnew

        from ..model_export import check_component_coverage
        from .models import attach_models
        from .project import write_project

        circuit = sample_board()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            original = root / "original"
            write_project(circuit, original, "fixture")
            attach_models(circuit, original / "fixture.kicad_pcb")
            relocated = root / "relocated"
            original.rename(relocated)
            board = pcbnew.LoadBoard(str(relocated / "fixture.kicad_pcb"))
            footprint = board.FindFootprintByReference("U1")
            assert footprint is not None
            self.assertEqual(len(footprint.Models()), 1)
            self.assertGreater((relocated / "models/TEST.step").stat().st_size, 0)
            glb = relocated / "fixture.glb"
            subprocess.run(
                (
                    "kicad-cli",
                    "pcb",
                    "export",
                    "glb",
                    "-o",
                    str(glb),
                    str(relocated / "fixture.kicad_pcb"),
                ),
                check=True,
                capture_output=True,
                text=True,
                timeout=60,
            )
            check_component_coverage(glb, {"U1"})
