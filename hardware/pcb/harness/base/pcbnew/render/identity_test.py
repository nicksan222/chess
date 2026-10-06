"""Check stable KiCad IDs for reviewable generated board files."""

import importlib.util
import re
import tempfile
import unittest
from pathlib import Path
from typing import cast

from pcb.harness import BoardComponent, Circuit, Placement
from pcb.harness.base.pcbnew.render.board_test import Pin, sample_board


@unittest.skipUnless(importlib.util.find_spec("pcbnew"), "KiCad Python module required")
class IdentityTest(unittest.TestCase):
    def test_every_serialized_uuid_has_a_unique_stable_replacement(self) -> None:
        """No native item can retain a random ID in a reviewed PCB file."""
        import pcbnew

        from pcb.harness.base.pcbnew.render.board import render_board
        from pcb.harness.base.pcbnew.render.identity import stable_uuid_map

        board = render_board(sample_board())
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "sample.kicad_pcb"
            pcbnew.SaveBoard(str(path), board)
            serialized = set(re.findall(r'\(uuid "([0-9a-f-]+)"\)', path.read_text()))
        mapping = stable_uuid_map(board)
        self.assertEqual(serialized, set(mapping))
        self.assertEqual(len(mapping.values()), len(set(mapping.values())))

    def test_existing_part_keeps_its_id_when_another_is_added(self) -> None:
        """A new unrelated footprint should not rekey an existing one."""
        from pcb.harness.base.pcbnew.outline import BoardOutline
        from pcb.harness.base.pcbnew.render.board import render_board
        from pcb.harness.base.pcbnew.render.identity import stable_uuid_map

        baseline = render_board(sample_board())
        original = baseline.FindFootprintByReference("U1")
        assert original is not None
        first = stable_uuid_map(baseline)[original.m_Uuid.AsString()]
        fixture = sample_board()
        template = cast(BoardComponent[Pin], fixture.components()[0])
        definition = template.definition
        expanded = Circuit(fixture.net_type, outline=BoardOutline(20, 10))
        for reference, x in (("U1", 0), ("U2", 5)):
            expanded.place(
                BoardComponent,
                reference=reference,
                definition=definition,
                placement=Placement(x, 0),
                purpose="identity fixture",
                pins=template.pins,
            )
        changed = render_board(expanded)
        existing = changed.FindFootprintByReference("U1")
        assert existing is not None
        self.assertEqual(stable_uuid_map(changed)[existing.m_Uuid.AsString()], first)

    def test_unmapped_uuid_is_rejected_before_normalizing(self) -> None:
        """An unsupported native item cannot retain a random serialized ID."""
        import pcbnew

        from pcb.harness.base.pcbnew.render.board import render_board
        from pcb.harness.base.pcbnew.render.identity import normalize_board_uuids

        board = render_board(sample_board())
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "sample.kicad_pcb"
            pcbnew.SaveBoard(str(path), board)
            path.write_text(
                path.read_text() + '\n(uuid "00000000-0000-0000-0000-000000000000")\n'
            )
            with self.assertRaisesRegex(ValueError, "unmapped"):
                normalize_board_uuids(board, path)
