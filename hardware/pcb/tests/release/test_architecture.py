"""Dependency boundaries keep KiCad optional and domain code independently testable."""

from __future__ import annotations

import ast
import subprocess
import sys
import unittest
from pathlib import Path

PCB_ROOT = Path(__file__).resolve().parents[2]
if str(PCB_ROOT) not in sys.path:
    sys.path.insert(0, str(PCB_ROOT))


class DependencyBoundaryTest(unittest.TestCase):
    def test_pcbnew_is_confined_to_the_kicad_adapter(self) -> None:
        offenders = []
        api_boundary = PCB_ROOT / "kicad" / "api.py"
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

    def test_reusable_domain_does_not_import_board_definitions(self) -> None:
        offenders = []
        for path in (PCB_ROOT / "domain").rglob("*.py"):
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

    def test_domain_and_hall_contract_tests_run_without_kicad(self) -> None:
        # A fresh process prevents cached native modules from hiding dependencies.
        script = """
import importlib.abc
import sys
import unittest

class NoKiCad(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname == "pcbnew":
            raise ModuleNotFoundError("KiCad deliberately unavailable", name=fullname)

sys.meta_path.insert(0, NoKiCad())
from domain.design import BoardDesign
from domain.schematic import render
from domain.schematic_symbols import render_symbol_library
from board import definition
design = definition.load()
assert isinstance(design, BoardDesign)
schematic = render(design)
assert schematic.startswith("(kicad_sch")
assert render_symbol_library(schematic).startswith("(kicad_symbol_lib")

from test_hall_banks import HallBankContractTest, HallBankCopperTest
from test_schematic_connectivity import SchematicConnectivityTest
suite = unittest.TestSuite(
    unittest.defaultTestLoader.loadTestsFromTestCase(test_class)
    for test_class in (HallBankContractTest, HallBankCopperTest, SchematicConnectivityTest)
)
result = unittest.TextTestRunner().run(suite)
assert result.wasSuccessful()
assert len(result.skipped) == 2, result.skipped
assert result.testsRun > len(result.skipped)
"""
        paths = (
            PCB_ROOT,
            PCB_ROOT.parent,
            PCB_ROOT / "tests",
            PCB_ROOT / "tests" / "layout",
            PCB_ROOT / "tests" / "model",
        )
        completed = subprocess.run(
            [
                sys.executable,
                "-B",
                "-c",
                f"import sys; sys.path[:0] = {list(map(str, paths))!r}\n" + script,
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)


if __name__ == "__main__":
    unittest.main()
