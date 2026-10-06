"""Series resistance from the supply to the board planes at a datasheet corner.

Every element is counted from the harness definition (shared/electronics/harness.py)
and the routed board: supply cord, jack contacts, harness wires, J4 contacts, fuse,
the DC_IN/DC_FUSED copper, the U74 eFuse on-resistance and its OUT copper (S4b: the
rocker only switches RUN, so it is not in the path). `low` is the least resistance
any datasheet allows (inrush worst case), `high` the most (voltage-drop worst
case). The +5V/GND planes are added by `PlaneMesh` where they matter.
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass
from typing import Literal, cast

import pcbnew

from shared.electronics.harness import POWER_HARNESS
from spice import datasheets
from spice.datasheets import Span
from spice.plane_mesh import OZ_MM, PCB_ROOT

Corner = Literal["low", "high"]
FUSES = {
    "0453002.MR": (
        datasheets.FUSE_0453002_COLD_OHMS,
        datasheets.FUSE_0453002_MELTING_I2T,
    ),
    "0454002.MR": (
        datasheets.FUSE_0454002_COLD_OHMS,
        datasheets.FUSE_0454002_MELTING_I2T,
    ),
}


def pick(span: Span, corner: Corner) -> float:
    """The low or high end of a datasheet span, for the `low` (inrush) or `high` (drop) corner."""
    return span.low if corner == "low" else span.high


def awg_area_m2(gauge: int) -> float:
    """ASTM B258 solid-equivalent conductor area."""
    diameter_mm = 0.127 * math.pow(92.0, (36 - gauge) / 39)
    return math.pi / 4 * (diameter_mm / 1000) ** 2


def copper_ohm_m(corner: Corner) -> float:
    """Copper resistivity at the corner's conductor temperature (20 C value, linear tempco)."""
    rise = pick(datasheets.CONDUCTOR_CELSIUS, corner) - 20.0
    return datasheets.COPPER_OHM_M_20C * (1 + datasheets.COPPER_TEMPCO_PER_K * rise)


def wire_ohms(gauge: int, metres: float, corner: Corner) -> float:
    """Resistance of `metres` of wire of AWG `gauge` at the corner."""
    return copper_ohm_m(corner) * metres / awg_area_m2(gauge)


def _outer_copper_m() -> float:
    """Outer-layer copper thickness in metres from `manufacturing.json` (minimum ounces)."""
    record = cast(
        dict[str, dict[str, float]],
        json.loads((PCB_ROOT / "definition/manufacturing.json").read_text()),
    )
    return OZ_MM * record["fabrication"]["outer_copper_oz_min"] / 1000
