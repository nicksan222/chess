"""Leaded parts that lie flat or stand up, with two holes.

Every one of these is derived from its lead diameter and hole pitch, so the
annular ring and drill clearance come from `base/rules.py` rather than being
restated per part.
"""

from __future__ import annotations

from base.footprint import two_pad_axial
from components.capacitor import CapacitorPin
from components.power_switch import PowerSwitchPin

ELECTROLYTIC_10MM = two_pad_axial(
    "radial 10 mm",
    "1000 uF radial electrolytic",
    pitch=5.0,
    lead_diameter=0.8,
    body=(10.5, 10.5),
    pin_numbers=tuple(CapacitorPin),
)

ROCKER_SWITCH = two_pad_axial(
    "SPST rocker THT",
    "Latching rocker power switch",
    pitch=12.7,
    lead_diameter=1.2,
    body=(19.5, 13.0),
    pin_numbers=tuple(PowerSwitchPin),
)
