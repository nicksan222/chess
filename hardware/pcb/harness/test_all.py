"""Standard unittest discovery entry point for the colocated ``*_test.py`` files.

The harness keeps each test beside the class or converter it explains. Python's
default discovery pattern is ``test*.py``, so this module bridges that standard
command to the required colocated naming convention. Run from the repository
root with ``PYTHONPATH=hardware python3 -m unittest discover
-s hardware/pcb/harness``.
"""

from __future__ import annotations

import unittest
from pathlib import Path


def load_tests(
    loader: unittest.TestLoader, _tests: unittest.TestSuite, _pattern: str | None
) -> unittest.TestSuite:
    """Load harness tests and future board-specific component tests."""
    hardware = Path(__file__).resolve().parents[2]
    suite = unittest.TestSuite()
    for directory in (hardware / "pcb" / "harness", hardware / "pcb" / "components"):
        suite.addTests(
            loader.discover(
                start_dir=str(directory),
                pattern="*_test.py",
                top_level_dir=str(hardware),
            )
        )
    return suite
