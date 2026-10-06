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


def top_side_violations() -> dict[str, str]:
    """Reference -> reason for every top-side part that does not clear the plate."""
    return _violations_in(_rows())


def _violations_in(rows: list[dict[str, str]]) -> dict[str, str]:
    """Top-side check over `rows`: each part's body, and its mated plug if any, must be
    shorter than the local gap minus a 0.5 mm margin. Separate from `top_side_violations`
    so a test can inject a fake row."""
    origin_x, origin_y = _board_offset(rows)
    violations: dict[str, str] = {}
    for row in rows:
        if row["Side"] != "top":
            continue
        reference = row["Ref"]
        spec = SPECS_BY_MPN.get(row["Val"])
        if spec is None or spec.body_mm is None:
            violations[reference] = f"{row['Val']} has no catalogued height"
            continue
        centre = (float(row["PosX"]) - origin_x, float(row["PosY"]) - origin_y)
        body = _square(centre, max(spec.body_mm[:2]))
        gap = _local_gap(body)
        height = spec.body_mm[2]
        if reference in BUTTON_REFERENCES:
            # The stem passes through the bezel; only the housing must clear.
            gap += cad.PANEL_BUTTON_RELIEF_DEPTH_MM
            height = cad.PANEL_BUTTON_BODY_MM[2]
        envelope = [(body, height), *mated_zones(reference, row["Val"])]
        for rect, slab_height in envelope:
            slab_gap = gap if rect == body else _local_gap(rect)
            if slab_height > slab_gap - TOP_SIDE_MARGIN_MM:
                violations[reference] = (
                    f"{slab_height:g} mm under a {slab_gap:g} mm gap at {rect}"
                )
    return violations


def _bottom_side_problem(rect: Rect, height: float) -> str | None:
    """Why a bottom-side slab does not fit the bay, or None."""
    limit = cad.PI_BAY_HEIGHT_MM - BOTTOM_SIDE_FLOOR_CLEARANCE_MM
    if height > limit:
        return f"{height:g} mm hangs below the {limit:g} mm bay limit"
    boss_reach = cad.PCB_SUPPORT_BOSS_DIAMETER_MM / 2.0 + 1.0
    for boss in cad.PCB_SUPPORT_POSITIONS_MM:
        gap = _gap_to(rect, boss)
        if gap < boss_reach:
            return f"{gap:.1f} mm from the support boss at {boss}"
    turned = int(cad.PI_ROTATION_DEG) % 180 == 90
    pi_x, pi_y = cad.PI_BOARD_SIZE_MM[:2]
    pi = _square(cad.PI_CENTER_MM, 0.0)
    reach_x = (pi_y if turned else pi_x) / 2.0 + cad.PI_CLEARANCE_MM
    reach_y = (pi_x if turned else pi_y) / 2.0 + cad.PI_CLEARANCE_MM
    if _overlaps(
        rect, (pi[0] - reach_x, pi[1] + reach_x, pi[2] - reach_y, pi[3] + reach_y)
    ):
        return "inside the Pi envelope"
    for name, keepout in cad.BOTTOM_SIDE_KEEPOUTS_MM.items():
        if _overlaps(rect, keepout):
            return f"inside the {name} bay keepout"
    wall = BOTTOM_SIDE_WALL_CLEARANCE_MM
    half_x = cad.CASE_CAVITY_SIZE_MM[0] / 2.0 - wall
    low_y = cad.CASE_CENTER_OFFSET_Y_MM - cad.CASE_CAVITY_SIZE_MM[1] / 2.0 + wall
    high_y = cad.CASE_CENTER_OFFSET_Y_MM + cad.CASE_CAVITY_SIZE_MM[1] / 2.0 - wall
    if rect[0] < -half_x or rect[1] > half_x or rect[2] < low_y or rect[3] > high_y:
        return "too close to the cavity wall"
    return None
