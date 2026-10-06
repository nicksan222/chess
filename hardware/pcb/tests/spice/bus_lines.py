"""Per-layer line parameters and per-net bus capacitance from the routed board.

Line impedance and capacitance follow IPC-2141 microstrip, Z0 = 87 / sqrt(er + 1.41)
x ln(5.98 h / (0.8 w + t)), with C = sqrt(eeff) / (c Z0) and delay sqrt(eeff) / c.
Outer layers use the Hammerstad effective permittivity; buried layers are fully
embedded (eeff = er). h is the distance to the nearest plane layer (In1-In3) in the
PCBWay stackup (`datasheets.STACKUP_DIELECTRICS`), planes In1-In3 and In6; a layer with no
plane on one side
is treated as microstrip to the nearer plane, which is the low-capacitance bound for
the stripline-like inner layers and is offset by the +10 % stackup allowance.
"""

from __future__ import annotations

import math
from collections import defaultdict
from dataclasses import dataclass

import pcbnew

from pcb.definition import rules
from spice import datasheets

LAYERS = ("F.Cu", "In1.Cu", "In2.Cu", "In3.Cu", "In4.Cu", "In5.Cu", "In6.Cu", "B.Cu")
# In6 is the LED_5V plane since S6, so B.Cu and In5 are now plane-referenced too.
PLANES = frozenset({"In1.Cu", "In2.Cu", "In3.Cu", "In6.Cu"})
LIGHT_MM_PER_NS = 299.792458
