"""The fresh mechanical snapshot survives the host-to-Blender boundary."""

import ast
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

from .pcb import PcbSnapshot


class PcbSnapshotTest(unittest.TestCase):
    def test_roundtrip_preserves_every_current_part_and_group(self) -> None:
        source = PcbSnapshot.current()
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "pcb.json"
            source.write(path)
            self.assertEqual(PcbSnapshot.read(path), source)

    def test_unknown_group_reference_is_rejected(self) -> None:
        source = PcbSnapshot.current()
        with self.assertRaisesRegex(ValueError, "unknown references"):
            replace(source, host_header="missing")

    def test_nonphysical_body_is_rejected(self) -> None:
        part = PcbSnapshot.current().parts[0]
        with self.assertRaisesRegex(ValueError, "positive"):
            replace(part, body_mm=(0.0, 1.0, 1.0))

    def test_cad_sources_parse_in_blenders_python_311(self) -> None:
        root = Path(__file__).resolve().parents[2]
        for path in root.rglob("*.py"):
            with self.subTest(path=path.relative_to(root)):
                ast.parse(path.read_text(), filename=str(path), feature_version=(3, 11))
