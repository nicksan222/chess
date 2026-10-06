"""Each harness cavity mates the board pad carrying the net the harness expects.

The pad is found by where JST's drawing (hand-typed rows in test_land_patterns) puts
the circuit of that number once the connector sits at its agreed placement, not by
pad number: a part on the bottom is seen mirrored from the top. So a mirrored
footprint, a renumbered land or a harness edit each fail here.
"""

import math
import unittest

import pcbnew

from board.test_land_patterns import GOLDEN
from pcb.definition import board, native
from shared import dimensions
from shared.electronics.harness import HARNESS_PARTS, HARNESSES

TOLERANCE_MM = 0.01
KEYS = {"J4": "POWER_HEADER", "J2": "OLED_HEADER"}


def _rotate(x: float, y: float, degrees: float) -> tuple[float, float]:
    """Rotate (x, y) by `degrees` about the origin."""
    c, s = math.cos(math.radians(degrees)), math.sin(math.radians(degrees))
    return (x * c - y * s, x * s + y * c)


def physical_circuit_mm(connector: str, circuit: str) -> tuple[float, float]:
    """Board-top position (shared mm) of a header circuit, from its drawing."""
    golden = next(g for g in GOLDEN if g.part_key == KEYS[connector])
    drawn = next(p for p in golden.pads if p.number == circuit).centre_mm
    assert drawn is not None
    placement = dimensions.PCB_STRIP_PLACEMENTS[connector]
    x, y = _rotate(*drawn, golden.frame_rotation_deg + placement.rotation_degrees)
    # Drawn from the mounting side: a part underneath is seen mirrored from above.
    if placement.bottom and not golden.drawn_from_board_top:
        x = -x
    return (placement.centre_mm[0] + x, placement.centre_mm[1] + y)


def pad_net_at(design: pcbnew.BOARD, connector: str, at: tuple[float, float]) -> str:
    footprint = design.FindFootprintByReference(connector)
    assert footprint is not None
    expected = native.point(*at)
    for pad in footprint.Pads():
        here = pad.GetPosition()
        if math.hypot(here.x - expected.x, here.y - expected.y) <= pcbnew.FromMM(
            TOLERANCE_MM
        ):
            return pad.GetNetname()
    return f"no {connector} pad at {at}"


class HarnessTest(unittest.TestCase):
    """Each harness cavity lands on the pad and net the harness definition expects."""

    def test_every_cavity_lands_on_its_net_by_physical_position(self) -> None:
        design = board.load()
        for wires in HARNESSES.values():
            for wire in wires:
                at = physical_circuit_mm(wire.connector, wire.cavity)
                with self.subTest(connector=wire.connector, cavity=wire.cavity):
                    self.assertEqual(pad_net_at(design, wire.connector, at), wire.net)

    def test_each_harness_fills_every_signal_cavity_once(self) -> None:
        for wires in HARNESSES.values():
            cavities = [(w.connector, w.cavity) for w in wires]
            self.assertEqual(len(cavities), len(set(cavities)))
        self.assertEqual(
            sorted(w.cavity for w in HARNESSES["Power entry"]), ["1", "2", "3", "4"]
        )
        self.assertEqual(
            sorted(w.cavity for w in HARNESSES["OLED"]), ["1", "2", "3", "4"]
        )

    def test_each_wire_has_its_own_colour_and_bom_line(self) -> None:
        # reviewer-s3c M-a/m-b: a swapped cavity must be visible, and every colour
        # is its own BOM line, bought by the spool and kitted at the cut length
        # (reviewer-s4 m8).
        for name, wires in HARNESSES.items():
            with self.subTest(harness=name):
                self.assertEqual(len({w.colour for w in wires}), len(wires))
                for w in wires:
                    self.assertIn(w.colour, w.wire.description)
                    self.assertEqual(w.wire.cut_length_mm, w.length_mm)
                    self.assertEqual(w.wire.purchase_unit, "100 ft spool")
                    self.assertEqual(HARNESS_PARTS[name][w.wire.key], 1)

    def test_a_mirrored_power_header_is_reported(self) -> None:
        # Mutation: the S3a placement (pads unmirrored on the bottom) put circuit
        # k where circuit 5 - k belongs, so cavity 1 (jack tip) met circuit 4 (RUN).
        design = board.load()
        header = design.FindFootprintByReference("J4")
        assert header is not None
        centre = header.GetPosition()
        for pad in header.Pads():
            at = pad.GetPosition()
            pad.SetPosition(pcbnew.VECTOR2I(2 * centre.x - at.x, at.y))
        at = physical_circuit_mm("J4", "1")
        self.assertEqual(pad_net_at(design, "J4", at), "RUN")


if __name__ == "__main__":
    unittest.main()
