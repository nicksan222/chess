"""Single-terminal board test points."""

from enum import StrEnum

from .base import BoardComponent


class TestPointPin(StrEnum):
    PROBE = "1"


class TestPoint(BoardComponent[TestPointPin]):
    pin_type = TestPointPin
