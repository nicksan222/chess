"""Shared test-point terminal identity."""

from enum import StrEnum

from pcb.spec.components import TEST_POINT
from pcb.spec.electronics.base import ElectronicComponent


class TestPointPin(StrEnum):
    PROBE = "1"


class TestPointComponent(ElectronicComponent[TestPointPin]):
    pin_type = TestPointPin
    specs = (TEST_POINT,)
