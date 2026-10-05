"""KiCad footprint and approved PCB binding for tvs diode."""

from pcb.definition.parts.land_patterns import two_terminal_smd
from pcb.definition.parts.part import PcbPart
from shared.components import TVS_6V8
from shared.electronics.passives import TvsDiodeComponent as TvsDiode
from shared.electronics.passives import TvsDiodePin

TVSDIODE_FOOTPRINT = two_terminal_smd(
    "SMB (DO-214AA)",
    "6 V unidirectional TVS diode",
    5.1,
    (2.2, 2.4),
    (4.6, 3.6),
    tuple(TvsDiodePin),
)

TVS_6V8_PART = PcbPart(
    TVS_6V8,
    TvsDiode,
    TVSDIODE_FOOTPRINT,
    "TVS",
    "SMBJ6.0A",
    "Input transient suppressor on the 5 V rail",
)
