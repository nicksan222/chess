"""Make the PCB harness available to repository-root unittest discovery.

Run ``python3 -m unittest discover`` from the repository root. Separate loaders
include harness behavior, automatic checks, and component-specific tests once.
"""

import unittest

from hardware.pcb.components.test_all import load_tests as component_tests
from hardware.pcb.harness.test_all import load_tests as harness_tests


def load_tests(
    loader: unittest.TestLoader, tests: unittest.TestSuite, pattern: str | None
) -> unittest.TestSuite:
    return unittest.TestSuite(
        (harness_tests(loader, tests, pattern), component_tests(loader, tests, pattern))
    )


__all__ = ("load_tests",)
