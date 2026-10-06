"""Make the PCB harness available to repository-root unittest discovery.

Run ``python3 -m unittest discover`` from the repository root. The delegated
loader includes the colocated harness and component ``*_test.py`` files.
"""

from hardware.pcb.harness.test_all import load_tests

__all__ = ("load_tests",)
