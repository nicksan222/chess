"""KiCad footprint and approved PCB binding for the input fuse F1.

Role: the last-resort fuse ahead of the eFuse on `DC_IN`. Land from the Littelfuse
drawing cited below. Pin identities: `shared/electronics/passives.py`.
"""

from pcb.definition.parts.land_patterns import two_terminal_smd
from pcb.definition.parts.part import DrawingView, PcbPart
from shared.components import FUSE_2A
from shared.electronics import ComponentReference
from shared.electronics.passives import FuseComponent as Fuse
from shared.electronics.passives import FusePin

# Littelfuse 451/453 (2009-01-07) p60 recommended pad layout: 1.96 x 3.15 pads,
# 2.95 gap (6.86 overall).
FUSE_FOOTPRINT = two_terminal_smd(
    "2410 fuse",
    "2 A very fast-acting surface-mount fuse",
    2.95 + 1.96,
    (1.96, 3.15),
    (6.1, 2.7),
    tuple(FusePin),
)

FUSE_2A_PART = PcbPart(
    FUSE_2A,
    Fuse,
    FUSE_FOOTPRINT,
    "FUSE",
    "2 A very fast-acting",
    "Input over-current protection on the jack tip",
    DrawingView.MOUNTING_SIDE,
)

INPUT_FUSE = Fuse(ComponentReference.INPUT_FUSE)
