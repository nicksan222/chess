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


def track_ohms(
    board: pcbnew.BOARD,
    net: str,
    corner: Corner,
    *,
    near: pcbnew.VECTOR2I | None = None,
    min_width_mm: float = 0.0,
) -> float:
    """Sum of a net's track resistances (optionally only within 8 mm of `near`).

    An upper bound for the high corner: parallel branches are counted in series.
    Tracks narrower than `min_width_mm` (bias stubs) carry no load and are skipped.
    """
    thickness = _outer_copper_m()
    total = 0.0
    for track in board.GetTracks():
        if track.GetNetname() != net or isinstance(track, pcbnew.PCB_VIA):
            continue
        if pcbnew.ToMM(track.GetWidth()) < min_width_mm:
            continue
        start, end = track.GetStart(), track.GetEnd()
        if near is not None and max(
            math.hypot(point.x - near.x, point.y - near.y) for point in (start, end)
        ) > pcbnew.FromMM(8.0):
            continue
        length = pcbnew.ToMM(round(math.hypot(end.x - start.x, end.y - start.y)))
        width = pcbnew.ToMM(track.GetWidth())
        total += copper_ohm_m(corner) * length / 1000 / (width / 1000 * thickness)
    return total


@dataclass(frozen=True)
class SeriesPath:
    """Supply-side resistance split into the + and return legs (ohms)."""

    positive: dict[str, float]
    ground: dict[str, float]

    @property
    def positive_ohms(self) -> float:
        """Total resistance of the positive leg."""
        return sum(self.positive.values())

    @property
    def ground_ohms(self) -> float:
        """Total resistance of the return leg."""
        return sum(self.ground.values())

    @property
    def total_ohms(self) -> float:
        """Positive plus return leg."""
        return self.positive_ohms + self.ground_ohms


def series_path(board: pcbnew.BOARD, fuse_mpn: str, corner: Corner) -> SeriesPath:
    """Supply-side resistance at `corner`: cord, jack and J4 contacts, harness wires, fuse, DC
    copper and the eFuse, split into the positive and return legs.
    """
    cord = wire_ohms(
        datasheets.PSU_CORD_AWG, pick(datasheets.PSU_CORD_METRES, corner), corner
    )
    contact = pick(datasheets.VH_CONTACT_OHMS, corner)
    jack = pick(datasheets.JACK_CONTACT_OHMS, corner)
    harness = {
        wire.net: wire_ohms(wire.gauge_awg, wire.length_mm / 1000, corner)
        for wire in POWER_HARNESS
    }
    efuse = board.FindFootprintByReference("U74")
    if efuse is None:
        raise ValueError("the S4b supply path needs U74")
    copper = corner == "high"
    positive = {
        "supply cord": cord,
        "jack centre contact": jack,
        "harness DC_IN": harness["DC_IN"],
        "J4 contact 1": contact,
        "DC_IN track": track_ohms(board, "DC_IN", corner),
        "fuse (cold x hot/tolerance allowance)": FUSES[fuse_mpn][0]
        * pick(datasheets.FUSE_RESISTANCE_FACTOR, corner),
        # The loop's branches are in parallel; the high corner counts all of it.
        "DC_FUSED copper": (
            track_ohms(board, "DC_FUSED", corner, min_width_mm=0.35) if copper else 0.0
        ),
        "eFuse RON [BEH]": pick(datasheets.EFUSE_RON_OHMS, corner),
        "U74 OUT copper": (
            track_ohms(board, "+5V", corner, near=efuse.GetPosition())
            if copper
            else 0.0
        ),
    }
    ground = {
        "supply cord": cord,
        "jack sleeve contact": jack,
        "harness GND": harness["GND"],
        "J4 contact 2": contact,
    }
    return SeriesPath(positive, ground)
