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


def _overlaps(a: Rect, b: Rect) -> bool:
    """True if two (x0, x1, y0, y1) rectangles share area (touching edges do not)."""
    return a[0] < b[1] and b[0] < a[1] and a[2] < b[3] and b[2] < a[3]


def _gap_to(rect: Rect, point: tuple[float, float]) -> float:
    """Chebyshev distance from a point to a rectangle (0 if inside), as used for bosses."""
    dx = max(rect[0] - point[0], point[0] - rect[1], 0.0)
    dy = max(rect[2] - point[1], point[1] - rect[3], 0.0)
    return max(dx, dy)


def mated_zones(reference: str, mpn: str) -> list[tuple[Rect, float]]:
    """Board-frame rectangles and heights of a connector's mated envelope."""
    zones = MATED_ENVELOPES.get(mpn, ())
    if not zones:
        return []
    placement = cad.PCB_STRIP_PLACEMENTS[reference]
    # The opening runs along local -Y, which a bottom-side X mirror leaves alone.
    dx, dy = _QUARTER_TURNS[int(placement.rotation_degrees) % 360]
    x, y = placement.centre_mm
    rects: list[tuple[Rect, float]] = []
    for zone in zones:
        mid = (zone.start_mm + zone.end_mm) / 2.0
        along = (zone.end_mm - zone.start_mm) / 2.0
        across = zone.width_mm / 2.0
        half_x = abs(dx) * along + abs(dy) * across
        half_y = abs(dy) * along + abs(dx) * across
        cx, cy = x + dx * mid, y + dy * mid
        rects.append(
            ((cx - half_x, cx + half_x, cy - half_y, cy + half_y), zone.height_mm)
        )
    return rects


def _rows() -> list[dict[str, str]]:
    """Rows of the generated position file."""
    with POSITIONS.open(newline="") as handle:
        return list(csv.DictReader(handle))


def _board_offset(rows: list[dict[str, str]]) -> tuple[float, float]:
    """Position-file origin, anchored on the shared panel button positions."""
    by_ref = {row["Ref"]: row for row in rows}
    offsets = {
        (
            round(float(by_ref[button.switch_reference]["PosX"]) - button.x_mm, 3),
            round(float(by_ref[button.switch_reference]["PosY"]) - button.y_mm, 3),
        )
        for button in cad.PANEL_BUTTONS
    }
    if len(offsets) != 1:
        raise AssertionError(f"Buttons disagree on the board origin: {offsets}")
    return offsets.pop()


def _local_gap(rect: Rect) -> float:
    """Space between the PCB top and whatever hangs from the plate above it."""
    module = _square(cad.PANEL_OLED_CENTER_MM, 0.0)
    half_x, half_y = (axis / 2.0 for axis in cad.PANEL_OLED_MODULE_MM[:2])
    module = (
        module[0] - half_x,
        module[1] + half_x,
        module[2] - half_y,
        module[3] + half_y,
    )
    if _overlaps(rect, module):
        return (
            cad.PCB_TO_PLATE_GAP_MM
            + cad.PANEL_OLED_RECESS_DEPTH_MM
            - cad.PANEL_OLED_MODULE_MM[2]
        )
    return cad.PCB_TO_PLATE_GAP_MM
