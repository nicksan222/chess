"""Independent bank pinout, source-graph, and actual routed-copper acceptance."""

import copy
import math
import unittest
from collections import defaultdict
from pathlib import Path

from board import definition
from components.footprints import TCA9554_SOIC
from components.tca9554 import Tca9554Pin
from domain import sources
from shared import dimensions, wiring
from shared.components import TCA9554

try:
    from kicad.api import pcbnew
except ModuleNotFoundError:  # Host-only unit runs do not install KiCad.
    pcbnew = None

if pcbnew is not None:
    from kicad import board as kicad


class HallBankContractTest(unittest.TestCase):
    def test_ti_dw0016a_pinout_and_land_pattern(self):
        # SCPS233E section 5 and DW0016A example layout, not inferred from enum order.
        expected = {
            "ADDRESS_0": "1",
            "ADDRESS_1": "2",
            "ADDRESS_2": "3",
            "P0": "4",
            "P1": "5",
            "P2": "6",
            "P3": "7",
            "GROUND": "8",
            "P4": "9",
            "P5": "10",
            "P6": "11",
            "P7": "12",
            "INTERRUPT": "13",
            "I2C_CLOCK": "14",
            "I2C_DATA": "15",
            "SUPPLY": "16",
        }
        self.assertEqual({pin.name: pin.value for pin in Tca9554Pin}, expected)
        self.assertEqual(TCA9554.mpn, "TCA9554DWR")
        self.assertEqual(TCA9554.require_body_mm(), (10.3, 7.5, 2.65))
        pads = {p.number: p for p in TCA9554_SOIC.pads}
        self.assertEqual(len(pads), 16)
        for number in range(1, 17):
            pad = pads[str(number)]
            self.assertEqual((pad.width, pad.height), (2.0, 0.6))
            self.assertAlmostEqual(pad.x, -4.65 if number <= 8 else 4.65)
            self.assertAlmostEqual(
                pad.y, 4.445 - (number - 1 if number <= 8 else 16 - number) * 1.27
            )

    def test_all_square_assignments_agree_with_reviewed_graph(self):
        design = definition.load()
        expanders = {
            c.spec.extras["Bank"]: c
            for c in design.components.values()
            if c.spec.part_key == "TCA9554"
        }
        seen = set()
        addresses = set()
        # Independent rank/file enumeration; each chip's left/right halves use P0–3/P4–7.
        package_pins = ("4", "5", "6", "7", "9", "10", "11", "12")
        for row in range(4):
            for column in range(2):
                index = row * 2 + column
                label = f"{'AE'[column]}{row * 2 + 1}-{'DH'[column]}{row * 2 + 2}"
                component = expanders[label]
                address = int(component.spec.extras["Address"], 16)
                self.assertEqual(address, 0x20 + index)
                addresses.add(address)
                for bit in range(3):
                    self.assertEqual(
                        design.connections.net_name(
                            (component.reference, str(bit + 1))
                        ),
                        "+3V3" if index & (1 << bit) else "GND",
                    )
                for channel, pin in enumerate(package_pins):
                    file = column * 4 + (channel // 4) * 2 + channel % 2
                    rank = row * 2 + (channel % 4) // 2
                    name = f"{'ABCDEFGH'[file]}{rank + 1}"
                    self.assertEqual(wiring.expander_of(file, rank), (index, channel))
                    self.assertEqual(
                        design.connections.net_name((component.reference, pin)),
                        f"SQ_{name}",
                    )
                    self.assertNotIn(name, seen)
                    seen.add(name)
        self.assertEqual(len(seen), 64)
        self.assertEqual(addresses, set(range(0x20, 0x28)))
        self.assertNotIn(wiring.OLED_ADDRESS, addresses)

    def test_generation_rejects_swapped_hall_channels(self):
        contract = copy.deepcopy(sources.netlist())
        signals = [
            c for c in contract["connections"] if (c["name"] or "").startswith("SQ_")
        ]
        signals[0]["pads"], signals[1]["pads"] = signals[1]["pads"], signals[0]["pads"]
        with self.assertRaisesRegex(ValueError, "incorrect Hall mapping"):
            definition.from_contract(contract)

    def test_generation_rejects_hall_supply_or_ground_as_signal(self):
        for other_pin in ("1", "3"):
            with self.subTest(other_pin=other_pin):
                contract = copy.deepcopy(sources.netlist())
                for connection in contract["connections"]:
                    for endpoint in connection["pads"]:
                        if endpoint[0] == "HS1":
                            endpoint[1] = {"2": other_pin, other_pin: "2"}.get(
                                endpoint[1], endpoint[1]
                            )
                with self.assertRaisesRegex(
                    ValueError, "A1-D2: A1 is not attached to its Hall sensor output"
                ):
                    definition.from_contract(contract)

    def test_expanders_and_caps_clear_mechanical_supports(self):
        design = definition.load()
        for component in design.components.values():
            if (
                component.spec.part_key != "TCA9554"
                and "For" not in component.spec.extras
            ):
                continue
            x0, y0, x1, y1 = component.placement.courtyard()
            for x, y in dimensions.PCB_SUPPORT_POSITIONS_MM:
                dx, dy = max(x0 - x, 0, x - x1), max(y0 - y, 0, y - y1)
                self.assertGreater(
                    math.hypot(dx, dy), dimensions.PCB_SUPPORT_BOSS_DIAMETER_MM / 2
                )


@unittest.skipUnless(pcbnew is not None, "KiCad pcbnew is not installed")
class HallBankCopperTest(unittest.TestCase):
    def test_generated_hall_copper_is_local_and_shorter_than_quadrant_baseline(self):
        board = pcbnew.LoadBoard(
            str(Path(__file__).resolve().parents[2] / "generated/chess-board.kicad_pcb")
        )
        lengths = defaultdict(float)
        vias = 0
        for track in board.GetTracks():
            name = track.GetNetname()
            if not name.startswith("SQ_"):
                continue
            file, rank = wiring.parse_square(name[3:])
            # Independent 160 x 80 mm bank rectangles, inset by router's 1 mm edge margin.
            left = -160 + (file // 4) * 160
            bottom = -160 + (rank // 2) * 80
            if isinstance(track, pcbnew.PCB_VIA):
                vias += 1
            else:
                lengths[name] += pcbnew.ToMM(track.GetLength())
            for point in (track.GetStart(), track.GetEnd()):
                x = pcbnew.ToMM(point.x) - kicad.ORIGIN_X_MM
                y = kicad.ORIGIN_Y_MM - pcbnew.ToMM(point.y)
                self.assertTrue(left + 1 <= x <= left + 159, (name, x))
                self.assertTrue(bottom + 1 <= y <= bottom + 79, (name, y))
        self.assertEqual(len(lengths), 64)
        self.assertLess(sum(lengths.values()), 4000.0)  # Baseline measured 4835.7 mm.
        self.assertLess(max(lengths.values()), 100.0)  # Baseline SQ_E1 130.7 mm.
        self.assertLessEqual(vias, 128)


if __name__ == "__main__":
    unittest.main()
