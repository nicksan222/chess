"""Surface-mount input over-current fuse F1."""

from enum import StrEnum

from .base import BoardComponent, ComponentReference


class FusePin(StrEnum):
    UNFUSED_INPUT = "1"
    FUSED_OUTPUT = "2"


class Fuse(BoardComponent[FusePin]):
    pin_type = FusePin


INPUT_FUSE = Fuse(ComponentReference.INPUT_FUSE)
