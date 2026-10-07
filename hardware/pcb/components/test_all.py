"""Discover only the component-specific, colocated unit tests."""

import unittest
from pathlib import Path


def load_tests(
    loader: unittest.TestLoader, _tests: unittest.TestSuite, _pattern: str | None
) -> unittest.TestSuite:
    hardware = Path(__file__).resolve().parents[2]
    return loader.discover(
        str(hardware / "pcb" / "components"),
        pattern="*_test.py",
        top_level_dir=str(hardware),
    )
