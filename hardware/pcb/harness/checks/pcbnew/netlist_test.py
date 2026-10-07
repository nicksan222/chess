"""Mismatched schematic exports must never rewrite a saved PCB."""

import importlib.util
import tempfile
import unittest
from pathlib import Path

from pcb.harness.base.pcbnew.render.board_test import sample_board


@unittest.skipUnless(importlib.util.find_spec("pcbnew"), "KiCad required")
class NetlistTest(unittest.TestCase):
    def test_wrong_reference_is_rejected_before_touching_board(self) -> None:
        from pcb.harness.checks.pcbnew.netlist import apply_netlist

        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            board = output / "board.kicad_pcb"
            board.write_text("previous reviewed board")
            netlist = output / "netlist.xml"
            netlist.write_text(
                '<export><nets><net name="+3V3"><node ref="WRONG" pin="1"/></net>'
                '<net name="GND"><node ref="U1" pin="2"/></net></nets></export>'
            )
            with self.assertRaisesRegex(ValueError, "differs from declared"):
                apply_netlist(sample_board(), netlist, board, output / "netlist.json")
            self.assertEqual(board.read_text(), "previous reviewed board")
            self.assertFalse((output / "netlist.json").exists())

    def test_duplicate_net_cannot_replace_an_earlier_bad_assignment(self) -> None:
        from pcb.harness.checks.pcbnew.netlist import apply_netlist

        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            netlist = output / "netlist.xml"
            netlist.write_text(
                '<export><nets><net name="+3V3"><node ref="WRONG" pin="1"/></net>'
                '<net name="+3V3"><node ref="U1" pin="1"/></net>'
                '<net name="GND"><node ref="U1" pin="2"/></net></nets></export>'
            )
            with self.assertRaisesRegex(ValueError, "duplicate schematic net"):
                apply_netlist(
                    sample_board(),
                    netlist,
                    output / "absent.kicad_pcb",
                    output / "netlist.json",
                )
