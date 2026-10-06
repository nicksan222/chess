"""Tests beside the concrete resistor kind and its simulation declaration."""

import unittest

from pcb.harness import (
    BoardRegistry,
    ComponentDefinition,
    Courtyard,
    NetConnection,
    Placement,
    Product,
)
from pcb.harness.base.net import Net
from pcb.harness.components.resistor import Resistor, ResistorPin


class Nets(Net):
    GROUND = "GND"
    POWER = "+3V3"


def resistor(
    board: BoardRegistry, *, ohms: float = 1000.0, tolerance: float = 1.0
) -> Resistor:
    kind = ComponentDefinition(
        Product("R1K", "Maker", "R-1K", "0603", (1.6, 0.8, 0.5), "sheet"),
        ResistorPin,
        Courtyard(2.0, 1.2),
    )
    return Resistor(
        registry=board,
        reference="R1",
        definition=kind,
        placement=Placement(0, 0),
        purpose="bias",
        pins={
            ResistorPin.TERMINAL_A: NetConnection(Nets.POWER),
            ResistorPin.TERMINAL_B: NetConnection(Nets.GROUND),
        },
        resistance_ohms=ohms,
        tolerance_percent=tolerance,
    )


class ResistorTest(unittest.TestCase):
    def test_valid_resistor_registers_and_supplies_its_value_to_spice_model(
        self,
    ) -> None:
        board = BoardRegistry()
        part = resistor(board)
        self.assertEqual(board.net_members(Nets.POWER)[0].reference, "R1")
        self.assertEqual(part.simulation_model().parameters[0].value, 1000.0)

    def test_zero_resistance_is_rejected_before_registration(self) -> None:
        board = BoardRegistry()
        with self.assertRaisesRegex(ValueError, "positive"):
            resistor(board, ohms=0)
        self.assertEqual(board.net_members(Nets.POWER), ())

    def test_tolerance_cannot_reach_one_hundred_percent(self) -> None:
        with self.assertRaisesRegex(ValueError, "between"):
            resistor(BoardRegistry(), tolerance=100)

    def test_same_purchased_part_cannot_have_conflicting_nominal_values(self) -> None:
        """A reused part number cannot mean both 1 kΩ and 10 kΩ."""
        board = BoardRegistry()
        first = resistor(board)
        with self.assertRaisesRegex(ValueError, "inconsistent product"):
            Resistor(
                registry=board,
                reference="R2",
                definition=first.definition,
                placement=Placement(3, 0),
                purpose="conflicting value",
                pins=first.pins,
                resistance_ohms=10000,
                tolerance_percent=1,
            )
        self.assertEqual(tuple(part.reference for part in board.components()), ("R1",))

    def test_same_product_and_value_can_be_reused(self) -> None:
        """Multiple placements of one real part share its nominal facts."""
        board = BoardRegistry()
        first = resistor(board)
        Resistor(
            registry=board,
            reference="R2",
            definition=first.definition,
            placement=Placement(3, 0),
            purpose="same purchased part",
            pins=first.pins,
            resistance_ohms=1000,
            tolerance_percent=1,
        )
        board.validate()
        self.assertEqual(len(board.components()), 2)
