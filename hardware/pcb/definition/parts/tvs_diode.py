"""KiCad footprint and approved PCB binding for the input TVS D1 (SMBJ12CA).

Role: bidirectional transient suppressor on `DC_FUSED`. Because it is bidirectional it
has no polarity mark; the land is the Littelfuse SMB land with the gap chosen below.
Pin identities: `shared/electronics/passives.py`.
"""

from pcb.definition.parts.land_patterns import two_terminal_smd
from pcb.definition.parts.part import DrawingView, PcbPart
from shared.components import TVS_12V0
from shared.electronics.passives import TvsDiodeComponent as TvsDiode
from shared.electronics.passives import TvsDiodePin

# Littelfuse SMBJ (2020-06-03) p5 solder pads: J = L >= 2.16, I >= 2.26, K <= 2.74.
# S4c (manufacturing review): a 2.30 mm gap K centres the leads. With G 5.21-5.59
# and E 0.76-1.52, the foot's inner edge (>= 1.085 from centre) overhangs the pad
# edge (1.15) by at most 0.065 mm, and the toe keeps 0.52-0.71 mm of pad.
SMBJ_PAD_GAP_MM = 2.30
TVSDIODE_FOOTPRINT = two_terminal_smd(
    "SMB (DO-214AA)",
    "12 V standoff bidirectional TVS diode (no polarity)",
    SMBJ_PAD_GAP_MM + 2.16,
    (2.16, 2.26),
    (4.6, 3.6),
    tuple(TvsDiodePin),
)


TVS_12V0_PART = PcbPart(
    TVS_12V0,
    TvsDiode,
    TVSDIODE_FOOTPRINT,
    "TVS",
    "SMBJ12CA",
    "Bidirectional transient suppressor on the eFuse input",
    DrawingView.MOUNTING_SIDE,
)
