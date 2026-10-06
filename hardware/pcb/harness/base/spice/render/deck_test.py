"""Tests beside assembly of complete, self-checking ngspice circuits."""

import tempfile
import unittest
from pathlib import Path

from pcb.harness import (
    BoardComponent,
    Circuit,
    ComponentDefinition,
    Courtyard,
    Placement,
    Product,
)
from pcb.harness.base.net import Net
from pcb.harness.base.spice.render.deck import render_deck, write_deck
from pcb.harness.components.resistor import Resistor, ResistorPin


class Nets(Net):
    GROUND = "GND"
    POWER = "+3V3"
    MID = "MID"


def divider_board(*, bounds: tuple[float, float] = (1.5, 1.8)) -> Circuit[Nets]:
    """Describe a divider and prove its midpoint under one nominal supply.

    The assertion is about the idealized 3.3 V operating point. It does not
    establish resistor tolerance corners or a physical board's copper behavior.
    """
    board = Circuit(Nets)
    kind = ComponentDefinition(
        Product("R1K", "Maker", "R-1K", "0603", (1.6, 0.8, 0.5), "sheet"),
        ResistorPin,
        Courtyard(2.0, 1.2),
    )
    board.place(
        Resistor,
        reference="R1",
        definition=kind,
        placement=Placement(0, 0),
        purpose="divider upper leg",
        pins={
            ResistorPin.TERMINAL_A: Nets.POWER,
            ResistorPin.TERMINAL_B: Nets.MID,
        },
        resistance_ohms=1000,
        tolerance_percent=1,
    )
    lower = board.place(
        Resistor,
        reference="R2",
        definition=kind,
        placement=Placement(2, 0),
        purpose="divider lower leg",
        pins={
            ResistorPin.TERMINAL_A: Nets.MID,
            ResistorPin.TERMINAL_B: Nets.GROUND,
        },
        resistance_ohms=1000,
        tolerance_percent=1,
    )
    with board.check("normal", ground=Nets.GROUND, purpose="nominal supply") as check:
        check.dc_supply("VPOWER", Nets.POWER, Nets.GROUND, volts=3.3)
        check.voltage_at(
            lower,
            ResistorPin.TERMINAL_A,
            between=bounds,
            because="midpoint must be near half supply",
        )
    return board


class DeckRenderTest(unittest.TestCase):
    """Check generated simulation evidence without claiming physical validation."""

    def test_complete_divider_deck_contains_parts_sources_measurement_and_assertion(
        self,
    ) -> None:
        """Every required element and the midpoint limit must reach the deck."""
        deck = divider_board().deck("normal")
        for line in (
            "VPOWER n1 0 DC 3.3",
            "R1 n1 n2 1000",
            "R2 n2 0 1000",
            ".op",
            "let result_r2_0 = v(n2)",
            "if result_r2_0 < 1.5",
            "if result_r2_0 > 1.8",
            ".end",
        ):
            self.assertIn(line, deck)

    def test_write_deck_creates_a_circuit_file(self) -> None:
        """Writing retains the resistor rows for an external simulator run."""
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "normal.cir"
            self.assertEqual(write_deck(divider_board(), "normal", path), path)
            self.assertIn("R1 n1 n2 1000", path.read_text())

    def test_close_assertion_bounds_remain_distinct(self) -> None:
        """The renderer cannot round two different limits into one value."""
        deck = divider_board(bounds=(1.0000001, 1.0000002)).deck("normal")
        self.assertIn("if result_r2_0 < 1.0000001", deck)
        self.assertIn("if result_r2_0 > 1.0000002", deck)

    def test_missing_scenario_is_rejected(self) -> None:
        """A misspelled check name cannot silently select a different setup."""
        with self.assertRaisesRegex(ValueError, "unknown SPICE scenario"):
            render_deck(divider_board(), "missing")

    def test_part_without_model_cannot_disappear_from_circuit(self) -> None:
        """An unmodeled component must stop conversion rather than be skipped."""
        board = divider_board()
        kind = ComponentDefinition(
            Product("EXTRA", "Maker", "X-1", "SMD", (1, 1, 1), "sheet"),
            ResistorPin,
            Courtyard(2, 2),
        )
        board.place(
            BoardComponent,
            reference="U3",
            definition=kind,
            placement=Placement(3, 0),
            purpose="unmodeled",
            pins={
                ResistorPin.TERMINAL_A: Nets.MID,
                ResistorPin.TERMINAL_B: Nets.GROUND,
            },
        )
        with self.assertRaisesRegex(ValueError, "no SPICE model"):
            render_deck(board, "normal")
