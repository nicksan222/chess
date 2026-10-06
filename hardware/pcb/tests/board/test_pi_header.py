"""J1 pad n lies under Pi header pin n, seen from the PCB top (no mirror error).

The Pi Zero 2 W hangs component side up below the board (RP-008358-DS-1 drawing,
transform in shared/dimensions/case.py). Its male header plugs up into J1 on the
PCB bottom, so each J1 hole must sit exactly at `pi_header_pin_xy(n)`. A plain
KiCad flip of a top-view footprint mirrors it; the negative case proves this test
catches that.
"""

import unittest

import pcbnew

from pcb.definition import board, native
from pcb.definition.parts.catalog import PCB_PARTS
from shared import dimensions

TOLERANCE_NM = 10_000  # 0.01 mm


def header_mismatches(footprint: pcbnew.FOOTPRINT) -> list[int]:
    """Pin numbers whose pad is not where the Pi's pin of that number lands."""
    wrong: list[int] = []
    for pad in footprint.Pads():
        number = int(pad.GetNumber())
        expected = native.point(*dimensions.pi_header_pin_xy(number))
        at = pad.GetPosition()
        if (
            abs(at.x - expected.x) > TOLERANCE_NM
            or abs(at.y - expected.y) > TOLERANCE_NM
        ):
            wrong.append(number)
    return sorted(wrong)


class PiHeaderTest(unittest.TestCase):
    """J1's pads sit under the Pi's pins; a mirrored header is detected."""

    def test_every_j1_pad_sits_under_the_pi_pin_of_the_same_number(self) -> None:
        native_board = board.load()
        header = native_board.FindFootprintByReference("J1")
        assert header is not None
        self.assertTrue(header.IsFlipped(), "J1 must be on the bottom side")
        self.assertEqual(len(list(header.Pads())), dimensions.PI_HEADER_PIN_COUNT)
        self.assertEqual(header_mismatches(header), [])
        # Pin 1 (3V3) and pin 2 (5V) must not trade places: that would put 5 V on
        # the Pi's 3.3 V rail.
        pads = {pad.GetNumber(): pad for pad in header.Pads()}
        self.assertEqual(pads["1"].GetNetname(), "+3V3")
        self.assertEqual(pads["2"].GetNetname(), "+5V")

    def test_a_plainly_flipped_header_is_reported_as_mirrored(self) -> None:
        scratch = pcbnew.BOARD()
        mirrored = PCB_PARTS["PI_ZERO_HEADER"].template.Duplicate()
        scratch.Add(mirrored)
        mirrored.SetPosition(native.point(*dimensions.PI_HEADER_CENTER_MM))
        mirrored.SetOrientationDegrees((dimensions.PI_ROTATION_DEG + 90.0) % 360.0)
        mirrored.Flip(mirrored.GetPosition(), pcbnew.FLIP_DIRECTION_LEFT_RIGHT)
        self.assertEqual(
            len(header_mismatches(mirrored)), dimensions.PI_HEADER_PIN_COUNT
        )


if __name__ == "__main__":
    unittest.main()
