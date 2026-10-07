"""CAM packaging must include every chosen layer and both drill types."""

import importlib.util
import subprocess
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path
from typing import cast
from zipfile import ZipFile

from pcb.harness import BoardComponent, Circuit, LandPattern, PadKind, Placement, Point
from pcb.harness.base.pcbnew.layout import BoardLayout, MountingHole
from pcb.harness.base.pcbnew.render.board_test import Nets, Pin, sample_board

from .fabrication import fabrication_layers, package_fabrication, write_fabrication


class FabricationTest(unittest.TestCase):
    def test_missing_inner_layer_prevents_an_archive(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for layer in fabrication_layers(8):
                if layer != "In6.Cu":
                    (
                        root
                        / f"sample-{layer.replace('.', '_').replace('_SilkS', '_Silkscreen')}.gbr"
                    ).write_text("%FSLAX46Y46*%\nM02*\n")
            archive = root / "output.zip"
            with self.assertRaisesRegex(ValueError, "In6.Cu"):
                package_fabrication(root, "sample", fabrication_layers(8), archive)
            self.assertFalse(archive.exists())

    def test_missing_nonplated_drill_prevents_an_archive(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for layer in fabrication_layers(2):
                (
                    root
                    / f"sample-{layer.replace('.', '_').replace('_SilkS', '_Silkscreen')}.gbr"
                ).write_text("%FSLAX46Y46*%\nM02*\n")
            (root / "sample-PTH.drl").write_text("M48\nM30\n")
            archive = root / "output.zip"
            with self.assertRaisesRegex(ValueError, "NPTH"):
                package_fabrication(root, "sample", fabrication_layers(2), archive)
            self.assertFalse(archive.exists())

    @unittest.skipUnless(
        importlib.util.find_spec("pcbnew"), "KiCad Python module required"
    )
    def test_native_exports_are_complete_and_zip_matches_files(self) -> None:
        sample = sample_board()
        part = cast(BoardComponent[Pin], sample.components()[0])
        pattern = part.definition.land_pattern
        assert pattern is not None
        circuit = Circuit(Nets, outline=sample.outline)
        circuit.place(
            BoardComponent,
            reference="J1",
            definition=replace(
                part.definition,
                land_pattern=LandPattern(
                    Pin,
                    (
                        replace(
                            pattern.pads[0], kind=PadKind.THROUGH_HOLE, drill_mm=0.4
                        ),
                        pattern.pads[1],
                    ),
                ),
            ),
            placement=Placement(0, 0),
            purpose="plated drill export",
            pins={Pin.A: Nets.POWER, Pin.B: Nets.GROUND},
        )
        circuit.layout = BoardLayout(holes=(MountingHole("H1", Point(5, 0), 2.0),))
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            board = root / "sample.kicad_pcb"
            circuit.write_board(board)

            def run(directory: Path, *arguments: str) -> None:
                subprocess.run(
                    arguments,
                    cwd=directory,
                    check=True,
                    capture_output=True,
                    timeout=30,
                )

            archive = write_fabrication(
                circuit, board, root, "sample", ("Prototype validation pending.",), run
            )
            with ZipFile(archive) as output:
                self.assertIsNone(output.testzip())
                names = set(output.namelist())
                self.assertEqual(
                    names, {path.name for path in (root / "fabrication").iterdir()}
                )
                self.assertIn("sample-PTH.drl", names)
                self.assertIn("sample-NPTH.drl", names)
                self.assertEqual(
                    sum(name.endswith(".gbr") for name in names),
                    len(fabrication_layers(2)),
                )
