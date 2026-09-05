"""KiCad's schematic parser independently checks the reviewed source graph."""

import shutil
import subprocess
import tempfile
import unittest
from collections import defaultdict
from pathlib import Path
from xml.etree import ElementTree

from board import artifacts, definition

try:
    from kicad.api import pcbnew
except ModuleNotFoundError:  # Host-only unit runs do not install KiCad.
    pcbnew = None


@unittest.skipUnless(pcbnew is not None, "KiCad pcbnew is not installed")
@unittest.skipUnless(shutil.which("kicad-cli"), "kicad-cli is not installed")
class SchematicConnectivityTest(unittest.TestCase):
    def test_exported_schematic_and_native_board_match_every_source_pin(self):
        design = definition.load()
        expected = defaultdict(set)
        for component in design.components.values():
            for logical, physical, _point, _pad in component.placement.pads():
                name = design.connections.net_name((component.reference, logical))
                expected[name].add((component.reference, physical))

        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "schematic.xml"
            subprocess.run(
                [
                    "kicad-cli",
                    "sch",
                    "export",
                    "netlist",
                    "--format",
                    "kicadxml",
                    "-o",
                    str(output),
                    str(artifacts.SCHEMATIC),
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            schematic = ElementTree.parse(output).getroot()
        exported = {
            net.attrib["name"]: {
                (node.attrib["ref"], node.attrib["pin"]) for node in net.findall("node")
            }
            for net in schematic.findall("./nets/net")
        }
        self.assertEqual(exported, expected)
        native = defaultdict(set)
        board = pcbnew.LoadBoard(str(artifacts.BOARD))
        for footprint in board.GetFootprints():
            for pad in footprint.Pads():
                if pad.GetAttribute() == pcbnew.PAD_ATTRIB_NPTH:
                    continue
                native[pad.GetNetname()].add(
                    (footprint.GetReference(), pad.GetNumber())
                )
        self.assertEqual(native, exported)


if __name__ == "__main__":
    unittest.main()
