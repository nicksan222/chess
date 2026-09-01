"""One square is a reusable, independently validated board assembly."""

from __future__ import annotations

import copy
import sys
import unittest
from pathlib import Path

PCB_ROOT = Path(__file__).resolve().parents[1]
if str(PCB_ROOT) not in sys.path:
    sys.path.insert(0, str(PCB_ROOT))

from core import placement, sources, square


class SquareAssemblyTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.components = sources.netlist()["components"]
        cls.shared = sources.dimensions()
        cls.centres = placement.square_centres(cls.shared)

    def assembly(self, name: str) -> square.SquareAssembly:
        return square.SquareAssembly.from_components(
            name,
            self.centres[name],
            self.shared.LED_POSITION_MM,
            self.components,
        )

    def test_one_square_contains_exactly_four_expected_parts(self) -> None:
        assembly = self.assembly("A1")
        self.assertEqual(assembly.led.reference, "U6")
        self.assertEqual(assembly.hall_sensor.reference, "HS1")
        self.assertEqual(assembly.led_bypass.reference, "C8")
        self.assertEqual(assembly.hall_bypass.reference, "C72")
        self.assertEqual(len(assembly.placements()), 4)

    def test_one_square_owns_all_of_its_relative_geometry(self) -> None:
        assembly = self.assembly("A1")
        placed = {part.reference: part for part in assembly.placements()}
        centre_x, centre_y = self.centres["A1"]
        led_x = centre_x + self.shared.LED_POSITION_MM[0]
        led_y = centre_y + self.shared.LED_POSITION_MM[1]

        self.assertEqual((placed["HS1"].x, placed["HS1"].y), (centre_x, centre_y))
        self.assertEqual((placed["U6"].x, placed["U6"].y), (led_x, led_y))
        self.assertEqual((placed["C8"].x, placed["C8"].y), (led_x, led_y - 8.0))
        self.assertEqual(
            (placed["C72"].x, placed["C72"].y),
            (centre_x, centre_y - 3.0),
        )

    def test_led_rotation_preserves_the_serpentine_chain(self) -> None:
        odd_rank_led = self.assembly("A1").placements()[0]
        even_rank_led = self.assembly("A2").placements()[0]
        self.assertEqual(odd_rank_led.rotation, 0.0)
        self.assertEqual(even_rank_led.rotation, 180.0)

    def test_every_square_builds_as_the_same_four_part_unit(self) -> None:
        assemblies = square.build_all(
            self.components,
            self.centres,
            self.shared.LED_POSITION_MM,
        )
        references = [
            part.reference for assembly in assemblies for part in assembly.placements()
        ]
        self.assertEqual(len(assemblies), 64)
        self.assertEqual(len(references), 64 * 4)
        self.assertEqual(len(set(references)), len(references))

    def test_missing_part_is_rejected_at_the_square_boundary(self) -> None:
        components = copy.deepcopy(self.components)
        components.pop("HS1")
        with self.assertRaisesRegex(ValueError, "exactly one Hall sensor; found 0"):
            square.SquareAssembly.from_components(
                "A1",
                self.centres["A1"],
                self.shared.LED_POSITION_MM,
                components,
            )

    def test_hall_bypass_must_name_the_sensor_in_its_square(self) -> None:
        components = copy.deepcopy(self.components)
        components["C72"]["extras"]["Sensor"] = "HS2"
        with self.assertRaisesRegex(ValueError, "not HS1"):
            square.SquareAssembly.from_components(
                "A1",
                self.centres["A1"],
                self.shared.LED_POSITION_MM,
                components,
            )


if __name__ == "__main__":
    unittest.main()
