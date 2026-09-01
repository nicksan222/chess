"""Every part the design contract places must have copper to land on.

The join between the two domains is the `package` string. These tests are what
stop a new part appearing in the bill of materials with no footprint behind it,
which would otherwise be discovered as a hole in the Gerbers.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

PCB_ROOT = Path(__file__).resolve().parents[1]
if str(PCB_ROOT) not in sys.path:
    sys.path.insert(0, str(PCB_ROOT))

import footprints  # noqa: E402
from core import rules, sources  # noqa: E402
from footprints.base import RECT, SHAPES  # noqa: E402


class CoverageTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.netlist = sources.netlist()

    def test_every_package_in_the_bom_has_a_footprint(self) -> None:
        packages = {
            entry["package"] for entry in self.netlist["components"].values()
        }
        missing = sorted(packages - set(footprints.CATALOG))
        self.assertEqual(missing, [], f"no footprint for {missing}")

    def test_every_footprint_is_used(self) -> None:
        """An unused footprint is dead weight; delete it or place the part."""
        packages = {
            entry["package"] for entry in self.netlist["components"].values()
        }
        unused = sorted(set(footprints.CATALOG) - packages)
        self.assertEqual(unused, [], f"unused footprints: {unused}")

    def test_every_contract_pin_has_a_pad(self) -> None:
        for reference, entry in self.netlist["components"].items():
            footprint = footprints.for_package(entry["package"])
            available = {pad.net_number for pad in footprint.pads}
            for connection in self.netlist["connections"]:
                for pad_reference, pin in connection["pads"]:
                    if pad_reference != reference:
                        continue
                    with self.subTest(reference=reference, pin=pin):
                        self.assertIn(pin, available)


class GeometryTest(unittest.TestCase):
    def test_shapes_and_sizes_are_sane(self) -> None:
        for package, footprint in footprints.CATALOG.items():
            with self.subTest(package=package):
                self.assertTrue(footprint.pads, "a footprint needs pads")
                self.assertTrue(footprint.description)
                for pad in footprint.pads:
                    self.assertIn(pad.shape, SHAPES)
                    self.assertGreater(pad.width, 0.0)
                    self.assertGreater(pad.height, 0.0)

    def test_through_hole_pads_keep_the_design_annular_ring(self) -> None:
        for package, footprint in footprints.CATALOG.items():
            for pad in footprint.pads:
                if not pad.plated_through:
                    continue
                with self.subTest(package=package, pad=pad.number):
                    drill_width, drill_height = pad.drill_size
                    self.assertGreaterEqual(
                        rules.annular_ring(pad.width, drill_width),
                        rules.PCBWAY_MIN_ANNULAR_RING_MM,
                    )
                    self.assertGreaterEqual(
                        rules.annular_ring(pad.height, drill_height),
                        rules.PCBWAY_MIN_ANNULAR_RING_MM,
                    )
                    self.assertGreaterEqual(drill_width, rules.PCBWAY_MIN_DRILL_MM)
                    self.assertGreaterEqual(drill_height, rules.PCBWAY_MIN_DRILL_MM)

    def test_pads_within_a_footprint_do_not_collide(self) -> None:
        for package, footprint in footprints.CATALOG.items():
            pads = footprint.pads
            for first in range(len(pads)):
                for second in range(first + 1, len(pads)):
                    a, b = pads[first], pads[second]
                    gap_x = abs(a.x - b.x) - (a.width + b.width) / 2.0
                    gap_y = abs(a.y - b.y) - (a.height + b.height) / 2.0
                    with self.subTest(package=package, pads=(a.number, b.number)):
                        self.assertGreater(
                            max(gap_x, gap_y), 0.0, "two pads overlap"
                        )

    def test_pads_fit_inside_their_courtyard(self) -> None:
        for package, footprint in footprints.CATALOG.items():
            width, height = footprint.courtyard
            for pad in footprint.pads:
                with self.subTest(package=package, pad=pad.number):
                    self.assertLessEqual(abs(pad.x) + pad.width / 2.0, width / 2.0)
                    self.assertLessEqual(abs(pad.y) + pad.height / 2.0, height / 2.0)

    def test_multi_pin_parts_mark_pin_one(self) -> None:
        """Pin 1 must be visibly different even before silkscreen is applied."""
        for package, footprint in footprints.CATALOG.items():
            if len(footprint.pads) < 3:
                continue
            with self.subTest(package=package):
                first = footprint.pad("1")
                self.assertEqual(first.shape, RECT)
                self.assertTrue(
                    any(pad.shape != first.shape for pad in footprint.pads[1:]),
                    "all pads look identical, so pin 1 is ambiguous",
                )

    def test_pj_102a_uses_the_manufacturer_slot_pattern(self) -> None:
        jack = footprints.for_package("5.5x2.0 mm THT")
        expected = {
            "1": (0.0, -3.0),
            "2": (0.0, 3.0),
            "3": (-4.7, 0.0),
        }
        self.assertEqual({pad.number: (pad.x, pad.y) for pad in jack.pads}, expected)
        self.assertEqual({pad.drill_size for pad in jack.pads}, {(1.0, 1.6)})


class RotationTest(unittest.TestCase):
    def test_a_quarter_turn_swaps_the_axes(self) -> None:
        pad = footprints.for_package("SOIC-28W 1.27 mm").pad("1")
        turned = pad.rotated(90)
        self.assertAlmostEqual(turned.x, -pad.y, places=4)
        self.assertAlmostEqual(turned.y, pad.x, places=4)
        self.assertAlmostEqual(turned.width, pad.height, places=4)

    def test_no_rotation_returns_the_same_pad(self) -> None:
        pad = footprints.for_package("SOIC-28W 1.27 mm").pad("1")
        self.assertIs(pad.rotated(0), pad)

    def test_courtyard_turns_with_the_part(self) -> None:
        footprint = footprints.for_package("2x20 2.54 mm THT")
        width, height = footprint.courtyard
        self.assertEqual(footprint.courtyard_at(90), (height, width))
        self.assertEqual(footprint.courtyard_at(0), (width, height))


class ExtraPadTest(unittest.TestCase):
    def test_suffixed_pads_share_their_base_pin_net(self) -> None:
        """A tactile switch's four legs are two shorted pairs."""
        tactile = footprints.for_package("6x6 mm THT")
        numbers = {pad.number for pad in tactile.pads}
        self.assertEqual(numbers, {"1", "1b", "2", "2b"})
        self.assertEqual({pad.net_number for pad in tactile.pads}, {"1", "2"})

    def test_a_plain_pin_number_is_its_own_net_number(self) -> None:
        for pad in footprints.for_package("SOIC-28W 1.27 mm").pads:
            self.assertEqual(pad.net_number, pad.number)


if __name__ == "__main__":
    unittest.main()
