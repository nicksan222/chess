"""Every PCB part fits the case: under the plate on top, in the bay below.

Placements come from the generated PCB position file and heights from the
shared component catalogue, so a part change on either side is checked here
without a CAD proxy having to model it.

Why: no 3D model of the populated PCB exists, so this is the check that a tall part (a
capacitor, a mated plug) does not collide with the plate above or the floor and bosses
below. It reads `pcb/generated/positions.csv`, so it is only as fresh as the last PCB
review: regenerate that first. Parts are boxed as squares over their larger body side
(conservative for any quarter-turn rotation; placements here are quarter turns). Evidence type: software test of catalogue heights; it
does not measure a real board.
"""

import csv
import unittest
from dataclasses import dataclass
from pathlib import Path

from core import dimensions as cad
from shared import components
from shared.components.spec import ComponentSpec

# Pick-and-place output of the PCB review; the board origin in it is re-anchored on the
# panel buttons (see `_board_offset`).
POSITIONS = Path(__file__).resolve().parents[2] / "pcb" / "generated" / "positions.csv"
# A part this close to the plate underside is treated as touching it.
TOP_SIDE_MARGIN_MM = 0.5

# Look up heights by MPN: the position file's value column is the part's MPN.
_CATALOGUE: list[object] = list(vars(components).values())
SPECS_BY_MPN = {
    spec.mpn: spec for spec in _CATALOGUE if isinstance(spec, ComponentSpec)
}
BUTTON_REFERENCES = {button.switch_reference for button in cad.PANEL_BUTTONS}
# Below the board the floor must stay this far from any part.
BOTTOM_SIDE_FLOOR_CLEARANCE_MM = 2.0
# The Pi header socket is checked as the Pi stack, by the shared transform.
PI_HEADER_REFERENCE = "J1"
# Bottom parts keep this far from the cavity wall.
BOTTOM_SIDE_WALL_CLEARANCE_MM = 1.0

Rect = tuple[float, float, float, float]


@dataclass(frozen=True, slots=True)
class MatedZone:
    """A slab of a mated connector, measured from the footprint origin along
    the opening direction (local -Y): the housing, then its wire exit."""

    start_mm: float
    end_mm: float
    width_mm: float
    height_mm: float


# Mated-plug envelopes per connector MPN, from the drawings cited on each entry (the
# bare header understates the space a plugged connector and its wires need).
MATED_ENVELOPES: dict[str, tuple[MatedZone, ...]] = {
    # JST SH SM04B-SRSS-TB + SHR-04V-S-B [eSH p1 side-entry assembly, mated 2.95
    # high and 6.25 long; p3 header 4.25 deep]: housing from the opening face
    # (3.24) to its rear (5.25), then 2.0 mm for AWG28 wires (OD 0.8) leaving at
    # mid-height to dress down under the OLED module.
    "SM04B-SRSS-TB": (
        MatedZone(3.24, 5.25, 6.0, 2.95),
        MatedZone(5.25, 7.25, 6.0, 1.95),
    ),
    # JST VH B4PS-VH + VHR-4N (s3a-interface.md H1): body y 127..138 about the
    # 132.45 origin, plug to y 148.5 at 10.5 mated, wire bend to y 152.
    "B4PS-VH": (
        MatedZone(-5.45, 16.05, 15.8, 10.5),
        MatedZone(16.05, 19.55, 15.8, 10.5),
    ),
}
# Direction of a connector's opening (local -Y) in the board frame for each placement
# rotation; placements here are always quarter turns.
_QUARTER_TURNS = {0: (0.0, -1.0), 90: (1.0, 0.0), 180: (0.0, 1.0), 270: (-1.0, 0.0)}


def _square(centre: tuple[float, float], side: float) -> Rect:
    """A square over the larger body side covers any rotation of the body."""
    half = side / 2.0
    return (centre[0] - half, centre[0] + half, centre[1] - half, centre[1] + half)
