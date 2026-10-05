"""KiCad footprint and approved PCB binding for fuse."""

from pcb.definition.parts.land_patterns import two_terminal_smd
from pcb.definition.parts.part import PcbPart
from shared.components import FUSE_2A
from shared.electronics import ComponentReference
from shared.electronics.passives import FuseComponent as Fuse
from shared.electronics.passives import FusePin

FUSE_FOOTPRINT = two_terminal_smd(
    "2410 fuse",
    "2 A time-delay surface-mount fuse",
    6.6,
    (2.7, 3.2),
    (6.1, 2.7),
    tuple(FusePin),
)

FUSE_2A_PART = PcbPart(
    FUSE_2A,
    Fuse,
    FUSE_FOOTPRINT,
    "FUSE",
    "2 A time-delay",
    "Input over-current protection matched to the 2.5 A jack",
)

INPUT_FUSE = Fuse(ComponentReference.INPUT_FUSE)
