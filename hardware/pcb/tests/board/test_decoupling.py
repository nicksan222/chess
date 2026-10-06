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

    @staticmethod
    def _close(
        supply: pcbnew.PAD, ground: pcbnew.PAD, rail: str, pads: dict[str, pcbnew.PAD]
    ) -> bool:
        """Rail pad near the supply pin and GND pad closing the loop to ground.

        For packages whose supply and ground pins sit at opposite corners (SOIC
        TCA9554/AHCT125) the return closes through the GND plane: both the cap GND
        pad and the device ground pin must reach In1 by a via within
        FANOUT_VIA_REACH_MM (checked in the test), and no distance term is applied.
        """
        if set(pads) != {rail, "GND"}:
            return False
        near = _edge_gap(_box(supply), _box(pads[rail])) <= BYPASS_EDGE_MAX_MM
        part = supply.GetParentFootprint().GetFieldText("PartKey")
        if part in DIAGONAL_RAIL_KEYS:
            return near
        loop_limit = _edge_gap(_box(supply), _box(ground)) + BYPASS_EDGE_MAX_MM
        return near and _edge_gap(_box(ground), _box(pads["GND"])) <= loop_limit

    def _match(
        self,
        devices: list[tuple[str, pcbnew.PAD, pcbnew.PAD, str]],
        capacitors: dict[str, dict[str, pcbnew.PAD]],
        assigned: dict[str, str],
    ) -> None:
        """Augmenting-path bipartite matching: every device its own capacitor."""
        owner = {cap: device for device, cap in assigned.items()}

        def augment(device: int, seen: set[str]) -> bool:
            """Try to give `device` a capacitor, moving an earlier owner to another one if needed (augmenting path)."""
            reference, supply, ground, rail = devices[device]
            for cap, pads in capacitors.items():
                if cap in seen or not self._close(supply, ground, rail, pads):
                    continue
                seen.add(cap)
                holder = owner.get(cap)
                if holder is None or augment(
                    next(i for i, d in enumerate(devices) if d[0] == holder), seen
                ):
                    owner[cap] = reference
                    assigned[reference] = cap
                    return True
            return False

        for index, device in enumerate(devices):
            if device[0] not in assigned:
                augment(index, set())

    def test_every_supply_pin_has_its_own_close_bypass_capacitor(self) -> None:
        devices = self._devices()
        # Banks, U5, U75 (S6b), LEDs, Hall sensors.
        self.assertEqual(len(devices), 8 + 1 + 1 + 64 + 64)
        assigned: dict[str, str] = {}
        # 100 nF parts are the intended high-frequency bypass; 10 uF only as fallback.
        for key in BYPASS_PREFERENCE:
            self._match(devices, self._capacitors(key), assigned)
        for reference, supply, ground, rail in devices:
            with self.subTest(reference=reference, check="rails"):
                self.assertEqual(supply.GetNetname(), rail)
                self.assertEqual(ground.GetNetname(), "GND")
            with self.subTest(reference=reference, check="bypass loop"):
                self.assertIn(reference, assigned, "no capacitor closes the loop")
            if reference not in assigned:
                continue
            capacitor = self.routed.FindFootprintByReference(assigned[reference])
            assert capacitor is not None
            for pad in (supply, ground, *capacitor.Pads()):
                with self.subTest(reference=reference, pad=pad.GetNumber()):
                    self.assertTrue(pad.IsOnLayer(pcbnew.F_Cu))
                    self.assertTrue(
                        self._has_fanout_via(pad),
                        f"{pad.GetParentFootprint().GetReference()}-"
                        f"{pad.GetNumber()} has no {pad.GetNetname()} via within "
                        f"{FANOUT_VIA_REACH_MM} mm",
                    )


if __name__ == "__main__":
    unittest.main()
