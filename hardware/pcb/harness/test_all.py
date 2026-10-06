"""Standard unittest discovery entry point for the colocated ``*_test.py`` files.

The harness keeps behavior tests beside the class or converter they explain.
Automatic catalog checks live in ``checks/`` and use ``test_*.py``. This bridge
loads both suites during standard discovery; the components package has its own
bridge for component-specific tests. For offline harness behavior checks use
``discover -s hardware/pcb/harness -t hardware -p '*_test.py'``.
"""

from __future__ import annotations

import unittest
from pathlib import Path


def load_tests(
    loader: unittest.TestLoader, _tests: unittest.TestSuite, _pattern: str | None
) -> unittest.TestSuite:
    """Load harness behavior tests and the automatic declaration checks."""
    hardware = Path(__file__).resolve().parents[2]
    suite = unittest.TestSuite()
    for directory, pattern in (
        (hardware / "pcb" / "harness", "*_test.py"),
        (hardware / "pcb" / "harness" / "checks", "test_*.py"),
    ):
        suite.addTests(
            loader.discover(
                start_dir=str(directory),
                pattern=pattern,
                top_level_dir=str(hardware),
            )
        )
    return suite
