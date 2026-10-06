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

from board.copper_flow import max_flow

PCB_ROOT = Path(__file__).resolve().parents[2]

K_OUTER = 0.048
K_INNER = 0.024
RISE_C = 10.0
MM2_TO_MIL2 = (1000 / 25.4) ** 2
OZ_MM = 0.035
VIA_WALL_MM = 0.018
FUSE_AMPS = 2.0
# U74 ILIM maximum (TPS259474, RILM 1.65 kOhm): the highest current it lets flow
# for longer than its 1.6 ms ITIMER blanking (S6d).
LED_SWITCH_AMPS = 2.2

# Loads fed from the planes through plated pins: part key -> pads sharing the load.
LOAD_ENTRIES = {"PI_ZERO_HEADER": ("2", "4")}
# Parts that conduct the full supply current in a fault before the fuse opens.
FAULT_PATH_KEYS = frozenset({"TVS_12V0"})
# part key -> pad -> datasheet maximum current through that pin (A).
DEVICE_PIN_AMPS = {
    # SK9822-A Rev 01: 3 x 18 mA ("18MA", conservative over §10's 17) + 1 mA IDD.
    "SK9822": {"4": 0.055, "3": 0.055},
    # SCPS233E §6.3 recommended operating: continuous current through VCC 80 mA,
    # through GND 200 mA.
    "TCA9554": {"16": 0.080, "8": 0.200},
    "AHCT125": {"14": 0.050, "7": 0.050},  # SCLS264R §6.1 VCC or GND current
    # SLVSDC7H §6.1 output current 5 mA: a conservative stand-in, as the supply
    # current itself is microamps.
    "HALL_SENSOR": {"1": 0.005, "3": 0.005},
}


def ampacity(area_mm2: float, *, outer: bool) -> float:
    """IPC-2221 current for a conductor cross-section at RISE_C."""
    k = K_OUTER if outer else K_INNER
    return k * math.pow(RISE_C, 0.44) * math.pow(area_mm2 * MM2_TO_MIL2, 0.725)


def _copper_mm(outer: bool) -> float:
    """Copper thickness (mm): the outer or inner minimum ounces from `manufacturing.json`."""
    record = cast(
        dict[str, dict[str, float]],
        json.loads((PCB_ROOT / "definition/manufacturing.json").read_text()),
    )
    fab = record["fabrication"]
    return OZ_MM * (fab["outer_copper_oz_min"] if outer else fab["inner_copper_oz_min"])


class AmpacityTest(unittest.TestCase):
    """Copper current capacity of the power path on the routed board (see the module docstring for the method)."""

    routed: ClassVar[pcbnew.BOARD]

    @classmethod
    def setUpClass(cls) -> None:
        """Load the published routed board once."""
        output = Path(os.environ.get("PCB_OUTPUT", PCB_ROOT / "generated"))
        cls.routed = pcbnew.LoadBoard(str(output / "chess-board.kicad_pcb"))

    def _parts(self, keys: Collection[str]) -> list[pcbnew.FOOTPRINT]:
        """Placed footprints whose part key is in `keys`; fails if there are none (so a renamed part cannot make a check vacuous)."""
        found = [
            footprint
            for footprint in self.routed.GetFootprints()
            if footprint.HasFieldByName("PartKey")
            and footprint.GetFieldText("PartKey") in keys
        ]
        self.assertTrue(found, f"no placed part for {keys}")
        return found
