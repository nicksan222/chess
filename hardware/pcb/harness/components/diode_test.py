"""Tests beside the generic anode-to-cathode diode component kind."""

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
from pcb.harness.components.diode import Diode, DiodePin


class Nets(Net):
    INPUT = "INPUT"
    OUTPUT = "OUTPUT"


def diode(board: BoardRegistry, saturation: float = 1e-12) -> Diode:
    kind = ComponentDefinition(
        Product("D_GENERIC", "Maker", "D-1", "SOD", (2, 1, 1), "sheet"),
        DiodePin,
        Courtyard(3, 2),
    )
    return Diode(
        registry=board,
        reference="D1",
        definition=kind,
        placement=Placement(0, 0),
        purpose="rectification",
        pins={
            DiodePin.ANODE: NetConnection(Nets.INPUT),
            DiodePin.CATHODE: NetConnection(Nets.OUTPUT),
        },
        saturation_current_amperes=saturation,
        ideality_factor=1.5,
        series_resistance_ohms=0.1,
    )


class DiodeTest(unittest.TestCase):
    def test_model_orders_anode_before_cathode(self) -> None:
        board = BoardRegistry()
        part = diode(board)
        self.assertEqual(
            part.simulation_model().terminals, (DiodePin.ANODE, DiodePin.CATHODE)
        )
        self.assertEqual(board.net_members(Nets.INPUT)[0].reference, "D1")

    def test_zero_saturation_current_does_not_register(self) -> None:
        board = BoardRegistry()
        with self.assertRaisesRegex(ValueError, "saturation current"):
            diode(board, 0)
        self.assertEqual(board.net_members(Nets.INPUT), ())

    def test_nonfinite_saturation_current_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "saturation current"):
            diode(BoardRegistry(), float("nan"))
