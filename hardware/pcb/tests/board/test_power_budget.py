"""Check the allowed LED load against the approved physical supply."""

import os
import unittest
from fractions import Fraction
from pathlib import Path
from typing import TypedDict, cast

from shared.components import POWER_SUPPLY
from shared.json_values import parse_json

PCB_ROOT = Path(__file__).resolve().parents[2]


class PowerSettings(TypedDict):
    supply_amps: float
    led_global_brightness_max: str


class ManufacturingRecord(TypedDict):
    power: PowerSettings


class PartRecord(TypedDict):
    part_key: str


class BoardRecord(TypedDict):
    components: dict[str, PartRecord]


class NetlistRecord(TypedDict):
    projects: dict[str, BoardRecord]


class PowerBudgetTest(unittest.TestCase):
    def test_approved_led_limit_has_supply_and_fuse_headroom(self) -> None:
        manufacturing = cast(
            ManufacturingRecord,
            parse_json((PCB_ROOT / "definition/manufacturing.json").read_text()),
        )
        output = Path(os.environ.get("PCB_OUTPUT", PCB_ROOT / "generated"))
        record = cast(NetlistRecord, parse_json((output / "netlist.json").read_text()))
        components = record["projects"]["board"]["components"]
        power = manufacturing["power"]
        brightness = Fraction(power["led_global_brightness_max"])

        # The approved GST12A05-P1J supply and 0453002.MR fuse are each
        # rated 2 A. A replacement supply needs a reviewed rating here.
        approved_supply_ratings = {"GST12A05-P1J": 2.0}
        self.assertIn(POWER_SUPPLY.mpn, approved_supply_ratings)
        self.assertEqual(
            power["supply_amps"], approved_supply_ratings[POWER_SUPPLY.mpn]
        )
        self.assertEqual(components["F1"]["part_key"], "FUSE_2A")
        self.assertGreaterEqual(brightness, 0)
        self.assertLessEqual(brightness, 1)

        led_count = sum(part["part_key"] == "SK9822" for part in components.values())
        self.assertEqual(led_count, 64)
        # Conservative input budget: 450 mA Pi/logic plus 60 mA per LED at
        # full white. Require 20% continuous-current margin at the allowed cap.
        allowed_amps = 0.45 + led_count * 0.06 * float(brightness)
        self.assertLessEqual(allowed_amps, 0.8 * power["supply_amps"])


if __name__ == "__main__":
    unittest.main()
