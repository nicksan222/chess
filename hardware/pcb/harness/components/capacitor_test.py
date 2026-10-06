"""Tests beside the generic two-terminal capacitor component kind."""

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
from pcb.harness.components.capacitor import Capacitor, CapacitorPin


class Nets(Net):
    GROUND = "GND"
    POWER = "+3V3"


def capacitor(board: BoardRegistry, farads: float = 1e-7) -> Capacitor:
    kind = ComponentDefinition(
        Product("C100N", "Maker", "C-100N", "0603", (1.6, 0.8, 0.8), "sheet"),
        CapacitorPin,
        Courtyard(2.0, 1.2),
    )
    return Capacitor(
        registry=board,
        reference="C1",
        definition=kind,
        placement=Placement(0, 0),
        purpose="local decoupling",
        pins={
            CapacitorPin.TERMINAL_A: NetConnection(Nets.POWER),
            CapacitorPin.TERMINAL_B: NetConnection(Nets.GROUND),
        },
        capacitance_farads=farads,
        rated_volts=10,
    )


class CapacitorTest(unittest.TestCase):
    def test_registers_with_capacitance_in_its_simulation_model(self) -> None:
        board = BoardRegistry()
        part = capacitor(board)
        self.assertEqual(board.net_members(Nets.POWER)[0].reference, "C1")
        self.assertEqual(part.simulation_model().parameters[0].value, 1e-7)

    def test_zero_capacitance_does_not_register(self) -> None:
        board = BoardRegistry()
        with self.assertRaisesRegex(ValueError, "positive"):
            capacitor(board, 0)
        self.assertEqual(board.net_members(Nets.POWER), ())

    def test_nonfinite_capacitance_does_not_register(self) -> None:
        with self.assertRaisesRegex(ValueError, "finite"):
            capacitor(BoardRegistry(), float("nan"))

    def test_same_purchased_capacitor_cannot_have_different_voltage_rating(
        self,
    ) -> None:
        """A rating is a product fact even though the ideal SPICE model omits it."""
        board = BoardRegistry()
        first = capacitor(board)
        with self.assertRaisesRegex(ValueError, "inconsistent product"):
            Capacitor(
                registry=board,
                reference="C2",
                definition=first.definition,
                placement=Placement(3, 0),
                purpose="conflicting rating",
                pins=first.pins,
                capacitance_farads=1e-7,
                rated_volts=25,
            )
        self.assertEqual(tuple(part.reference for part in board.components()), ("C1",))
