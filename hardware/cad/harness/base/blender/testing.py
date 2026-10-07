"""Run board-specific native tests before publishing generated artifacts."""

import unittest
from pathlib import Path


def run_tests(directory: Path) -> int:
    suite = unittest.defaultTestLoader.discover(
        str(directory),
        pattern="*_test.py",
        top_level_dir=str(Path(__file__).resolve().parents[4]),
    )
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if not result.wasSuccessful() or result.skipped or not result.testsRun:
        raise RuntimeError("Native CAD tests failed, skipped or were not discovered")
    return result.testsRun
