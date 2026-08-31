"""Input over-current fuse holder F1."""

from enum import StrEnum

from .base import BoardComponent, ComponentReference


class FuseHolderPin(StrEnum):
    UNFUSED_INPUT = "1"
    FUSED_OUTPUT = "2"


class FuseHolder(BoardComponent[FuseHolderPin]):
    pin_type = FuseHolderPin


INPUT_FUSE = FuseHolder(ComponentReference.INPUT_FUSE)
