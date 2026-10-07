"""Automatic catalogue-body and mated-connector checks against the current PCB.

Checks use fresh PCB declarations, including negative regression cases; electronic
envelopes are conservative catalogue approximations, not physical measurements.
"""

import math

from cad.harness.base.pcb import PcbPart, PcbSnapshot
from shared import dimensions as cad

# A part this close to the plate underside is treated as touching it.
TOP_SIDE_MARGIN_MM = 0.5

# Below the board the floor must stay this far from any part.
BOTTOM_SIDE_FLOOR_CLEARANCE_MM = 2.0
# The Pi header socket is checked as the Pi stack, by the shared transform.
# Bottom parts keep this far from the cavity wall.
BOTTOM_SIDE_WALL_CLEARANCE_MM = 1.0

Rect = tuple[float, float, float, float]


def square_envelope(centre: tuple[float, float], side: float) -> Rect:
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


def mated_zones(part: PcbPart) -> list[tuple[Rect, float]]:
    """Board-frame rectangles and heights of a connector's mated envelope."""
    zones = part.mated_zones
    if not zones:
        return []
    # Opening direction is local -Y; the bottom-side X mirror leaves it unchanged.
    angle = math.radians(part.rotation_degrees)
    dx, dy = math.sin(angle), -math.cos(angle)
    x, y = part.position_mm
    rects: list[tuple[Rect, float]] = []
    for start, end, width, height in zones:
        mid = (start + end) / 2.0
        along = (end - start) / 2.0
        across = width / 2.0
        half_x = abs(dx) * along + abs(dy) * across
        half_y = abs(dy) * along + abs(dx) * across
        cx, cy = x + dx * mid, y + dy * mid
        rects.append(((cx - half_x, cx + half_x, cy - half_y, cy + half_y), height))
    return rects


def local_gap(rect: Rect) -> float:
    """Space between the PCB top and whatever hangs from the plate above it."""
    # The complete display module is mounted outside the plate.
    return cad.PCB_TO_PLATE_GAP_MM


def top_side_violations(snapshot: PcbSnapshot | None = None) -> dict[str, str]:
    """Every current top-side body and mated connector must clear the plate."""
    pcb = PcbSnapshot.current() if snapshot is None else snapshot
    violations: dict[str, str] = {}
    for part in pcb.parts:
        if part.bottom:
            continue
        body = square_envelope(part.position_mm, max(part.body_mm[:2]))
        gap = local_gap(body)
        height = part.body_mm[2]
        if part.panel_passage is not None:
            # The stem passes through the bezel; only its housing must clear.
            gap += cad.PANEL_BUTTON_RELIEF_DEPTH_MM
            height = (part.housing_mm or part.body_mm)[2]
        envelope = [(body, height), *mated_zones(part)]
        for rect, slab_height in envelope:
            slab_gap = gap if rect == body else local_gap(rect)
            if slab_height > slab_gap - TOP_SIDE_MARGIN_MM:
                violations[part.reference] = (
                    f"{slab_height:g} mm under a {slab_gap:g} mm gap at {rect}"
                )
    return violations


def bottom_side_problem(rect: Rect, height: float) -> str | None:
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
    pi = square_envelope(cad.PI_CENTER_MM, 0.0)
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


def bottom_side_violations(snapshot: PcbSnapshot | None = None) -> dict[str, str]:
    """Every bottom body/connector must fit the bay; the host stack is checked in Blender."""
    pcb = PcbSnapshot.current() if snapshot is None else snapshot
    violations: dict[str, str] = {}
    for part in pcb.parts:
        if not part.bottom or part.reference == pcb.host_header:
            continue
        body = square_envelope(part.position_mm, max(part.body_mm[:2]))
        for rect, height in [(body, part.body_mm[2]), *mated_zones(part)]:
            problem = bottom_side_problem(rect, height)
            if problem is not None:
                violations[part.reference] = problem
    return violations
