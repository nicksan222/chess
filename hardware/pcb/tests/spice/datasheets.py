"""Device internals and limits quoted from manufacturer documents.

Each constant names its source. SPICE models build multi-pad devices from these
facts and the board's actual pad geometry/nets, never from the net names alone.
"""

from __future__ import annotations

from dataclasses import dataclass

from shared.electronics import sk9822

# E-Switch TL1105 series (2.28.2018). p24 specifications: contact resistance
# 100 mOhm max, insulation resistance 100 MOhm min. p25 drawing/schematic: leads
# 1-2 and 3-4 sit 6.50 mm apart and are internally connected; the dome bridges the
# pairs, whose leads sit 4.50 mm apart (holes +/-0.1 mm).
TL1105_CONTACT_OHMS_MAX = 0.1
TL1105_INSULATION_OHMS_MIN = 100e6
TL1105_STRAPPED_LEAD_PITCH_MM = 6.5
TL1105_BRIDGED_LEAD_PITCH_MM = 4.5
TL1105_LEAD_PITCH_TOLERANCE_MM = 0.3
# The internal strap is a single stamped terminal; its resistance is not specified,
# so it is modelled as the contact maximum, the most pessimistic stated value.
TL1105_STRAP_OHMS = TL1105_CONTACT_OHMS_MAX


@dataclass(frozen=True)
class Span:
    """A quantity's datasheet minimum and maximum (corners, not a nominal)."""

    low: float
    high: float
