"""Single-terminal board test points."""

from enum import StrEnum

from base.component import BoardComponent


class TestPointPin(StrEnum):
    PROBE = "1"


class TestPoint(BoardComponent[TestPointPin]):
    pin_type = TestPointPin
