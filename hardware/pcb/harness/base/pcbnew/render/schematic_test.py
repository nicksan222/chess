"""Schematic conversion must retain declared nets and explained unused pins."""

import tempfile
import unittest
from pathlib import Path
from typing import cast

from pcb.harness import BoardComponent, Circuit, NoConnect
from pcb.harness.base.pcbnew.render.board_test import Nets, Pin, sample_board
from pcb.harness.base.pcbnew.render.schematic import write_schematic


class SchematicTest(unittest.TestCase):
    def test_writes_embedded_symbols_and_exact_declared_net_labels(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            paths = write_schematic(sample_board(), target, "tiny")
            self.assertTrue(paths.root.is_file())
            self.assertEqual(len(paths.sheets), 1)
            sheet = paths.sheets[0].read_text()
            self.assertIn("(lib_symbols", sheet)
            self.assertIn('(global_label "GND"', sheet)
            self.assertIn('(reference "U1")', sheet)

    def test_same_declaration_generates_identical_schematic_bytes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            first, second = root / "first", root / "second"
            first.mkdir()
            second.mkdir()
            a = write_schematic(sample_board(), first, "tiny")
            b = write_schematic(sample_board(), second, "tiny")
            self.assertEqual(a.root.read_bytes(), b.root.read_bytes())
            self.assertEqual(a.sheets[0].read_bytes(), b.sheets[0].read_bytes())

    def test_unused_pin_gets_no_connect_marker_and_no_net_label(self) -> None:
        source = sample_board()
        part = cast(BoardComponent[Pin], source.components()[0])
        declaration = Circuit(Nets, outline=source.outline)
        declaration.place(
            BoardComponent,
            reference=part.reference,
            definition=part.definition,
            placement=part.placement,
            purpose=part.purpose,
            pins={Pin.A: Nets.POWER, Pin.B: NoConnect("unused fixture terminal")},
        )
        with tempfile.TemporaryDirectory() as directory:
            files = write_schematic(declaration, Path(directory), "tiny")
            content = files.sheets[0].read_text()
            self.assertEqual(content.count("(no_connect "), 1)
            self.assertNotIn('(global_label "GND"', content)
            self.assertTrue((Path(directory) / "board.kicad_sym").is_file())
            self.assertTrue((Path(directory) / "sym-lib-table").is_file())
