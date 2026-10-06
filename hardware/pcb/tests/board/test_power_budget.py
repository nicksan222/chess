"""Check the allowed LED load against the approved physical supply.

Why: the approved LED brightness cap lives in `manufacturing.json`; this test ties it to
the supply and fuse ratings the board actually uses, so swapping the supply without a
reviewed rating, or raising the cap, fails here rather than at the bench.
"""

import os
import unittest
from fractions import Fraction
from pathlib import Path
from typing import TypedDict, cast

from spice import datasheets

from shared.components import POWER_SUPPLY
from shared.electronics import sk9822
from shared.json_values import parse_json

PCB_ROOT = Path(__file__).resolve().parents[2]


class PowerSettings(TypedDict):
    """The `power` section of `manufacturing.json`: supply rating and LED brightness cap."""

    supply_amps: float
    led_global_brightness_max: str


class ManufacturingRecord(TypedDict):
    """The part of `manufacturing.json` this test reads."""

    power: PowerSettings


class PartRecord(TypedDict):
    """A netlist component entry (only its part key is read)."""

    part_key: str


class BoardRecord(TypedDict):
    """The netlist's board projection (components only)."""

    components: dict[str, PartRecord]


class NetlistRecord(TypedDict):
    """The netlist file's top level."""

    projects: dict[str, BoardRecord]


class PowerBudgetTest(unittest.TestCase):
    """The approved LED limit against the supply and fuse ratings."""

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
        # Input budget: the Pi/logic allowance (ASSUMPTION "Host and logic
        # current") plus each LED's full-white current (SK9822-A: 3 x 18 mA + 1 mA
        # static) scaled by the cap. Require 20% continuous-current margin at the
        # allowed cap.
        per_led = 3 * sk9822.CHANNEL_AMPS_MAX + sk9822.STATIC_AMPS
        allowed_amps = datasheets.HOST_AND_LOGIC_AMPS + led_count * per_led * float(
            brightness
        )
        self.assertLessEqual(allowed_amps, 0.8 * power["supply_amps"])


if __name__ == "__main__":
    unittest.main()
