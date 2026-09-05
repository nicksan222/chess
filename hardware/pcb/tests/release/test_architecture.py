"""Dependency boundaries keep KiCad optional and domain code independently testable."""

from __future__ import annotations

import ast
import sys
import unittest
from pathlib import Path

PCB_ROOT = Path(__file__).resolve().parents[2]
if str(PCB_ROOT) not in sys.path:
    sys.path.insert(0, str(PCB_ROOT))


class DependencyBoundaryTest(unittest.TestCase):
    def test_pcbnew_is_confined_to_the_kicad_adapter(self) -> None:
        offenders = []
        api_boundary = PCB_ROOT / "base" / "kicad" / "api.py"
        for path in PCB_ROOT.rglob("*.py"):
            if path == api_boundary or "tests" in path.parts:
                continue
            tree = ast.parse(path.read_text())
            for node in ast.walk(tree):
                if isinstance(node, ast.Import) and any(
                    name.name == "pcbnew" for name in node.names
                ):
                    offenders.append(path.relative_to(PCB_ROOT))
                if isinstance(node, ast.ImportFrom) and node.module == "pcbnew":
                    offenders.append(path.relative_to(PCB_ROOT))
        self.assertEqual(offenders, [])

    def test_reusable_base_does_not_import_board_definitions(self) -> None:
        offenders = []
        for path in (PCB_ROOT / "base").rglob("*.py"):
            tree = ast.parse(path.read_text())
            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
                    root = node.module.split(".", 1)[0]
                    if root == "board":
                        offenders.append(path.relative_to(PCB_ROOT))
                if isinstance(node, ast.Import) and any(
                    name.name.split(".", 1)[0] == "board" for name in node.names
                ):
                    offenders.append(path.relative_to(PCB_ROOT))
        self.assertEqual(offenders, [])

    def test_domain_model_import_does_not_require_kicad(self) -> None:
        from base.design import BoardDesign
        from board import definition as board_definition

        design = board_definition.load()
        self.assertIsInstance(design, BoardDesign)
        self.assertGreater(len(design.components), 0)


if __name__ == "__main__":
    unittest.main()
