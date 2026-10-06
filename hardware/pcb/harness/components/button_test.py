"""Tests beside the generic two-contact button component kind."""

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
from pcb.harness.components.button import Button, ButtonPin, ButtonState


class Nets(Net):
    GROUND = "GND"
    INPUT = "INPUT"


def button(board: BoardRegistry, state: ButtonState = ButtonState.OPEN) -> Button:
    kind = ComponentDefinition(
        Product("BUTTON", "Maker", "B-1", "THT", (6, 6, 4), "sheet"),
        ButtonPin,
        Courtyard(8, 8),
    )
    return Button(
        registry=board,
        reference="SW1",
        definition=kind,
        placement=Placement(0, 0),
        purpose="user input",
        pins={
            ButtonPin.CONTACT_A: NetConnection(Nets.INPUT),
            ButtonPin.CONTACT_B: NetConnection(Nets.GROUND),
        },
        state=state,
        closed_resistance_ohms=0.05,
        open_resistance_ohms=1e12,
    )


class ButtonTest(unittest.TestCase):
    def test_open_state_uses_high_contact_resistance(self) -> None:
        board = BoardRegistry()
        part = button(board)
        self.assertEqual(part.simulation_model().parameters[0].value, 1e12)
        self.assertEqual(board.net_members(Nets.INPUT)[0].reference, "SW1")

    def test_closed_state_uses_low_contact_resistance(self) -> None:
        part = button(BoardRegistry(), ButtonState.CLOSED)
        self.assertEqual(part.simulation_model().parameters[0].value, 0.05)

    def test_invalid_state_does_not_register(self) -> None:
        board = BoardRegistry()
        with self.assertRaisesRegex(ValueError, "state"):
            button(board, "pressed")  # type: ignore[arg-type]
        self.assertEqual(board.net_members(Nets.INPUT), ())

    def test_same_button_product_allows_different_operating_states(self) -> None:
        """A pressed button is an operating condition, not a new part number."""
        board = BoardRegistry()
        first = button(board, ButtonState.OPEN)
        Button(
            registry=board,
            reference="SW2",
            definition=first.definition,
            placement=Placement(10, 0),
            purpose="second button",
            pins=first.pins,
            state=ButtonState.CLOSED,
            closed_resistance_ohms=0.05,
            open_resistance_ohms=1e12,
        )
        board.validate()
        self.assertEqual(len(board.components()), 2)
