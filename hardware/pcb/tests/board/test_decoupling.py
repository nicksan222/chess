"""Bypass-capacitor placement and plane fanout on the routed generated board.

Supply and ground pins come from the datasheets cited in `test_land_patterns.py`
(TCA9554 16/8, SN74AHCT125 14/7, DRV5032 1/3, SK9822 4/3). The datasheets ask
for a 0.1 uF ceramic "close to" the supply pin without a number (TI SLVSDC7H §9,
SCPS233E §11; Opsco SPC/SK9822-A §12 "capacitance between beads is essential").
The stated limits below are this board's engineering rule, not datasheet values.
Each IC/LED gets its own nearest same-rail capacitor; no capacitor counts twice.
"""

import math
import os
import unittest
from pathlib import Path
from typing import ClassVar

import pcbnew

PCB_ROOT = Path(__file__).resolve().parents[2]

# part key -> (supply pad, supply net, ground pad)
SUPPLY_PINS = {
    "TCA9554": ("16", "+3V3", "8"),
    "AHCT125": ("14", "+5V", "7"),
    "HALL_SENSOR": ("1", "+3V3", "3"),
    "SK9822": ("4", "LED_5V", "3"),
    "LED_ENABLE_GATE": ("5", "+5V", "2"),
}
BYPASS_PREFERENCE = ("CAP_100N", "CAP_10U")
# Supply and ground pins at opposite package corners (datasheet pinouts above).
DIAGONAL_RAIL_KEYS = frozenset({"TCA9554", "AHCT125"})

# Copper edge of the supply pad to copper edge of its capacitor's rail pad. The
# capacitor's GND pad must also close the loop: no farther from the device's ground
# pin than the device's own supply-to-ground pin gap plus this limit.
BYPASS_EDGE_MAX_MM = 3.0
# Copper edge of a supply/ground/capacitor pad to the centre of its own plane via.
FANOUT_VIA_REACH_MM = 2.0

Box = tuple[float, float, float, float]


def _box(pad: pcbnew.PAD) -> Box:
    """A pad's bounding box as (left, top, right, bottom) in mm."""
    box = pad.GetBoundingBox()
    return (
        pcbnew.ToMM(box.GetLeft()),
        pcbnew.ToMM(box.GetTop()),
        pcbnew.ToMM(box.GetRight()),
        pcbnew.ToMM(box.GetBottom()),
    )


def _edge_gap(a: Box, b: Box) -> float:
    """Edge-to-edge distance between two boxes (0 if they touch or overlap)."""
    dx = max(b[0] - a[2], a[0] - b[2], 0.0)
    dy = max(b[1] - a[3], a[1] - b[3], 0.0)
    return math.hypot(dx, dy)


def _point_gap(x: float, y: float, box: Box) -> float:
    """Distance from a point to a box (0 if inside)."""
    dx = max(box[0] - x, 0.0, x - box[2])
    dy = max(box[1] - y, 0.0, y - box[3])
    return math.hypot(dx, dy)


class DecouplingTest(unittest.TestCase):
    """Bypass-capacitor placement and plane fan-out on the routed board."""

    routed: ClassVar[pcbnew.BOARD]
    vias: ClassVar[dict[str, list[tuple[float, float]]]]

    @classmethod
    def setUpClass(cls) -> None:
        """Load the routed board and index its vias by net once."""
        output = Path(os.environ.get("PCB_OUTPUT", PCB_ROOT / "generated"))
        cls.routed = pcbnew.LoadBoard(str(output / "chess-board.kicad_pcb"))
        cls.vias = {}
        for item in cls.routed.GetTracks():
            if isinstance(item, pcbnew.PCB_VIA):
                at = item.GetPosition()
                cls.vias.setdefault(item.GetNetname(), []).append(
                    (pcbnew.ToMM(at.x), pcbnew.ToMM(at.y))
                )

    def _has_fanout_via(self, pad: pcbnew.PAD) -> bool:
        """True if a same-net via lies within reach of the pad's box (the pad has its own path to the plane)."""
        box = _box(pad)
        return any(
            _point_gap(x, y, box) <= FANOUT_VIA_REACH_MM
            for x, y in self.vias.get(pad.GetNetname(), [])
        )

    def _devices(self) -> list[tuple[str, pcbnew.PAD, pcbnew.PAD, str]]:
        """Each IC/LED supply pin as (reference, supply pad, ground pad, rail), from the datasheet pin table."""
        found: list[tuple[str, pcbnew.PAD, pcbnew.PAD, str]] = []
        for footprint in self.routed.GetFootprints():
            if not footprint.HasFieldByName("PartKey"):
                continue
            key = footprint.GetFieldText("PartKey")
            if key in SUPPLY_PINS:
                supply_number, rail, ground_number = SUPPLY_PINS[key]
                pads = {pad.GetNumber(): pad for pad in footprint.Pads()}
                found.append(
                    (
                        footprint.GetReference(),
                        pads[supply_number],
                        pads[ground_number],
                        rail,
                    )
                )
        return found

    def _capacitors(self, key: str) -> dict[str, dict[str, pcbnew.PAD]]:
        """Bypass candidates by reference, keyed by the net of each pad."""
        return {
            footprint.GetReference(): {
                pad.GetNetname(): pad for pad in footprint.Pads()
            }
            for footprint in self.routed.GetFootprints()
            if footprint.HasFieldByName("PartKey")
            and footprint.GetFieldText("PartKey") == key
        }
