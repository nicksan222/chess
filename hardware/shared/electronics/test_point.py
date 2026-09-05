"""Shared test-point terminal identity."""

from enum import StrEnum

from shared.components import TEST_POINT
from shared.electronics.base import ElectronicComponent


class TestPointPin(StrEnum):
    PROBE = "1"


class TestPointComponent(ElectronicComponent[TestPointPin]):
    pin_type = TestPointPin
    specs = (TEST_POINT,)
