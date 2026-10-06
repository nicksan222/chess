"""Copper current capacity of the power path on the routed generated board.

IPC-2221 (2003) §6.2 / Figure 6-4 curve fit: I = k * dT^0.44 * A^0.725, A in mil²,
k = 0.048 outer, 0.024 inner layers. The rise is held to 10 °C. Copper thickness
comes from manufacturing.json (1 oz = 0.035 mm). Plated via walls use PCBWay's
standard hole-wall copper floor, 0.018 mm (18-25 um on its capabilities page, per
the 2026-10-06 manufacturing review), below IPC-6012 Class 2's 0.020 mm average. The power path must carry the 0453002.MR rating of 2 A (Littelfuse
451/453, 2009-01-07): the routed copper from J4.1 to F1, from F1 to the U74 eFuse
IN and from U74 OUT into its +5V vias (parallel necks add: max-flow over the
tracks), the TVS fault path, J4's GND contact into its plane, and the Pi's 5 V
pins. Device fanouts carry each device's own datasheet maximum.
"""

import json
import math
import os
import unittest
from collections.abc import Collection, Sequence
from pathlib import Path
from typing import ClassVar, cast

import pcbnew
from spice.plane_mesh import (
    PLANE_LAYERS,
    connected_vias,
    power_entry_pads,
    spoke_width_mm,
    tracks_touching,
)
