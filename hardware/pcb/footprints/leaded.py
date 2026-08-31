"""Leaded parts that lie flat or stand up, with two holes.

Every one of these is derived from its lead diameter and hole pitch, so the
annular ring and drill clearance come from `core/rules.py` rather than being
restated per part.
"""

from __future__ import annotations

from .base import two_pad_axial

CERAMIC_DISC = two_pad_axial(
    "disc 2.54 mm",
    "100 nF ceramic disc capacitor",
    pitch=2.54,
    lead_diameter=0.5,
    body=(4.0, 4.0),
)

RESISTOR_AXIAL = two_pad_axial(
    "axial 1/4 W",
    "Quarter-watt axial resistor",
    pitch=10.16,
    lead_diameter=0.6,
    body=(6.5, 2.5),
)

# The reed lies along the square it senses. A 14 mm glass body needs its leads
# bent, so the pitch is wider than the body.
REED_AXIAL = two_pad_axial(
    "axial 14 mm",
    "Normally-open glass reed switch",
    pitch=17.78,
    lead_diameter=0.5,
    body=(17.78, 2.6),
)

TVS_AXIAL = two_pad_axial(
    "axial DO-15",
    "P6KE6.8A transient suppressor",
    pitch=10.16,
    lead_diameter=0.8,
    body=(7.5, 3.0),
)

ELECTROLYTIC_10MM = two_pad_axial(
    "radial 10 mm",
    "1000 uF radial electrolytic",
    pitch=5.0,
    lead_diameter=0.8,
    body=(10.5, 10.5),
)

ELECTROLYTIC_5MM = two_pad_axial(
    "radial 5 mm",
    "10 uF radial electrolytic",
    pitch=2.5,
    lead_diameter=0.6,
    body=(5.5, 5.5),
)

# A 5x20 mm cartridge in clips. The pitch is the clip spacing, not the fuse.
FUSE_HOLDER = two_pad_axial(
    "5x20 mm holder THT",
    "Panel fuse holder for a 5x20 mm cartridge",
    pitch=22.0,
    lead_diameter=1.0,
    body=(26.0, 8.0),
)

ROCKER_SWITCH = two_pad_axial(
    "SPST rocker THT",
    "Latching rocker power switch",
    pitch=12.7,
    lead_diameter=1.2,
    body=(19.5, 13.0),
)
