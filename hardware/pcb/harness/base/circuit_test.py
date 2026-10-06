"""Tests for the single board-authoring entry point."""

import unittest
from typing import cast

from pcb.harness import (
    BoardOutline,
    Circuit,
    ComponentDefinition,
    Courtyard,
    Net,
    Placement,
    Product,
)
from pcb.harness.base.spice.render.deck import render_deck
from pcb.harness.components.resistor import Resistor, ResistorPin


class Nets(Net):
    GROUND = "GND"
    POWER = "+3V3"
    MID = "MID"


def divider() -> Circuit[Nets]:
    """Build a complete typed example used by the authoring-path tests."""
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
        purpose="upper divider leg",
        pins={ResistorPin.TERMINAL_A: Nets.POWER, ResistorPin.TERMINAL_B: Nets.MID},
        resistance_ohms=1000,
        tolerance_percent=1,
    )
    lower = board.place(
        Resistor,
        reference="R2",
        definition=kind,
        placement=Placement(2, 0),
        purpose="lower divider leg",
        pins={ResistorPin.TERMINAL_A: Nets.MID, ResistorPin.TERMINAL_B: Nets.GROUND},
        resistance_ohms=1000,
        tolerance_percent=1,
    )
    with board.check("normal", ground=Nets.GROUND, purpose="nominal supply") as check:
        check.dc_supply("VPOWER", Nets.POWER, Nets.GROUND, volts=3.3)
        check.voltage_at(
            lower,
            ResistorPin.TERMINAL_A,
            between=(1.5, 1.8),
            because="midpoint must be near half supply",
        )
    return board


class CircuitTest(unittest.TestCase):
    """Exercise readable authoring and the complete path to simulation text."""

    def test_divider_is_a_complete_simulation_without_public_spice_types(self) -> None:
        """Placement plus a check yields registered parts and a concrete deck."""
        board = divider()
        # Both typed resistor declarations must enter the same circuit registry.
        self.assertEqual(
            tuple(part.reference for part in board.components()), ("R1", "R2")
        )
        deck = render_deck(board, "normal")
        # The deck contains a real midpoint probe; this is simulation setup
        # evidence, not a measurement from a manufactured board.
        self.assertIn("R1 n1 n2 1000", deck)
        self.assertIn("let result_r2_0 = v(n2)", deck)

    def test_outline_must_be_a_physical_outline(self) -> None:
        """The builder rejects malformed geometry before any part registers."""
        with self.assertRaisesRegex(ValueError, "outline"):
            Circuit(Nets, outline="20 by 10")  # type: ignore[arg-type]

    def test_duplicate_net_labels_are_rejected(self) -> None:
        """Enum aliases cannot hide two design names behind one board net."""

        class Ambiguous(Net):
            FIRST = "SIGNAL"
            SECOND = "SIGNAL"

        with self.assertRaisesRegex(ValueError, "duplicate net labels"):
            Circuit(Ambiguous)

    def test_builder_rejects_overlap_as_second_component_is_placed(self) -> None:
        """Board authors receive an error without invoking a separate check."""
        board = Circuit(Nets, outline=BoardOutline(20, 10))
        kind = ComponentDefinition(
            Product("R1K", "Maker", "R-1K", "0603", (1.6, 0.8, 0.5), "sheet"),
            ResistorPin,
            Courtyard(2, 1.2),
        )
        pins = {
            ResistorPin.TERMINAL_A: Nets.POWER,
            ResistorPin.TERMINAL_B: Nets.MID,
        }
        board.place(
            Resistor,
            reference="R1",
            definition=kind,
            placement=Placement(0, 0),
            purpose="first",
            pins=pins,
            resistance_ohms=1000,
            tolerance_percent=1,
        )
        with self.assertRaisesRegex(ValueError, "R1.*R2.*courtyard overlap"):
            board.place(
                Resistor,
                reference="R2",
                definition=kind,
                placement=Placement(1, 0),
                purpose="colliding second",
                pins=pins,
                resistance_ohms=1000,
                tolerance_percent=1,
            )
        self.assertEqual(tuple(part.reference for part in board.components()), ("R1",))

    def test_builder_rejects_net_from_another_enum(self) -> None:
        """The circuit rejects a ground net from another board enum."""

        class OtherNets(Net):
            POWER = "+3V3"

        board = Circuit(Nets)
        with self.assertRaisesRegex(ValueError, "board Net enum"):
            board.check(
                "wrong", ground=cast(Nets, OtherNets.POWER), purpose="wrong ground"
            )

    def test_unknown_check_has_a_board_author_facing_error(self) -> None:
        """Selecting an undeclared scenario reports the public check error."""
        with self.assertRaisesRegex(ValueError, "unknown circuit check"):
            divider().deck("typo")

    def test_failed_placement_with_foreign_net_leaves_board_empty(self) -> None:
        """A rejected placement does not leave a partial board declaration."""

        class OtherNets(Net):
            POWER = "+3V3"

        board = Circuit(Nets)
        kind = ComponentDefinition(
            Product("R1K", "Maker", "R-1K", "0603", (1.6, 0.8, 0.5), "sheet"),
            ResistorPin,
            Courtyard(2, 1),
        )
        with self.assertRaisesRegex(ValueError, "board Net enum"):
            board.place(
                Resistor,
                reference="R1",
                definition=kind,
                placement=Placement(0, 0),
                purpose="wrong net",
                pins={
                    ResistorPin.TERMINAL_A: OtherNets.POWER,
                    ResistorPin.TERMINAL_B: Nets.GROUND,
                },
                resistance_ohms=1000,
                tolerance_percent=1,
            )
        # A rejected component must not leave a partial board declaration.
        self.assertEqual(board.components(), ())

    def test_failed_check_does_not_register_partial_scenario(self) -> None:
        """An exception inside a check block prevents scenario registration."""
        board = Circuit(Nets)
        with (
            self.assertRaisesRegex(ValueError, "bad check"),
            board.check("broken", ground=Nets.GROUND, purpose="failure"),
        ):
            raise ValueError("bad check")
        with self.assertRaisesRegex(ValueError, "unknown SPICE scenario"):
            board.scenario("broken")

    def test_check_without_expectation_cannot_report_a_pass(self) -> None:
        """A stimulus without an assertion cannot become a registered check."""
        board = divider()
        with (
            self.assertRaisesRegex(ValueError, "expectation"),
            board.check("empty", ground=Nets.GROUND, purpose="empty proof") as check,
        ):
            check.dc_supply("V1", Nets.POWER, Nets.GROUND, volts=3.3)
        with self.assertRaisesRegex(ValueError, "unknown SPICE scenario"):
            board.scenario("empty")

    def test_voltage_check_rejects_pin_from_another_component_kind(self) -> None:
        """A measurement pin must belong to the placed component's pin enum."""
        from pcb.harness.components.diode import DiodePin

        board = divider()
        lower = cast(Resistor, board.components()[1])
        with (
            self.assertRaisesRegex(ValueError, "pin"),
            board.check("bad-pin", ground=Nets.GROUND, purpose="wrong pin") as check,
        ):
            check.voltage_at(
                lower,
                cast(ResistorPin, DiodePin.ANODE),
                between=(0, 1),
                because="must be typed",
            )

    def test_transient_check_describes_a_pulse_and_final_voltage(self) -> None:
        """A transient check renders its pulse, duration and final-time probe."""
        board = divider()
        lower = cast(Resistor, board.components()[1])
        with board.check("pulse", ground=Nets.GROUND, purpose="power pulse") as check:
            check.transient(duration_seconds=0.01, step_seconds=0.0001)
            check.pulse_supply(
                "VPULSE",
                Nets.POWER,
                Nets.GROUND,
                low_volts=0,
                high_volts=3.3,
                delay_seconds=0,
                rise_seconds=1e-6,
                fall_seconds=1e-6,
                high_seconds=0.02,
                period_seconds=0.03,
            )
            check.voltage_at(
                lower,
                ResistorPin.TERMINAL_A,
                between=(1.5, 1.8),
                because="midpoint after supply rises",
            )
        deck = board.deck("pulse")
        # The transient samples the midpoint at the final simulated instant.
        self.assertIn(".tran 0.0001 0.01", deck)
        self.assertIn("meas tran result_r2_0 FIND v(n2) AT=0.01", deck)

    def test_ac_check_describes_frequency_sweep_and_magnitude(self) -> None:
        """An AC check renders a sweep and maximum magnitude observation."""
        board = divider()
        lower = cast(Resistor, board.components()[1])
        with board.check(
            "response", ground=Nets.GROUND, purpose="small signal"
        ) as check:
            check.ac_sweep(start_hz=10, stop_hz=10000, points_per_decade=20)
            check.dc_supply("VPOWER", Nets.POWER, Nets.GROUND, volts=0, ac_volts=1)
            check.voltage_at(
                lower,
                ResistorPin.TERMINAL_A,
                between=(0.4, 0.6),
                because="half input magnitude",
            )
        deck = board.deck("response")
        # The AC assertion observes maximum voltage magnitude over the sweep.
        self.assertIn(".ac dec 20 10 10000", deck)
        self.assertIn("meas ac result_r2_0 MAX magnitude_result_r2_0", deck)

    def test_check_can_compare_two_typed_component_pins(self) -> None:
        """A voltage-between assertion names two typed component endpoints."""
        board = divider()
        upper = cast(Resistor, board.components()[0])
        lower = cast(Resistor, board.components()[1])
        with board.check(
            "drop", ground=Nets.GROUND, purpose="upper resistor drop"
        ) as check:
            check.dc_supply("VPOWER", Nets.POWER, Nets.GROUND, volts=3.3)
            check.voltage_between(
                upper,
                ResistorPin.TERMINAL_A,
                lower,
                ResistorPin.TERMINAL_A,
                between=(1.5, 1.8),
                because="upper resistor drops half the supply",
            )
        self.assertIn("v(n1,n2)", board.deck("drop"))

    def test_check_can_measure_current_through_its_supply(self) -> None:
        """A source-current assertion measures the named supply branch."""
        board = divider()
        with board.check("load", ground=Nets.GROUND, purpose="supply current") as check:
            supply = check.dc_supply("VPOWER", Nets.POWER, Nets.GROUND, volts=3.3)
            check.source_current(
                supply,
                between=(-0.002, -0.001),
                because="divider draws about 1.65 mA",
            )
        self.assertIn("i(VPOWER)", board.deck("load"))

    def test_analysis_must_be_selected_before_expectations(self) -> None:
        """Changing analysis after an expectation would make sampling ambiguous."""
        board = divider()
        lower = cast(Resistor, board.components()[1])
        with (
            self.assertRaisesRegex(ValueError, "before expectations"),
            board.check("late", ground=Nets.GROUND, purpose="late choice") as check,
        ):
            check.voltage_at(
                lower,
                ResistorPin.TERMINAL_A,
                between=(1, 2),
                because="midpoint",
            )
            check.transient(duration_seconds=1, step_seconds=0.1)

    def test_check_can_inject_current_without_raw_spice(self) -> None:
        """A current stimulus can be declared without writing simulator syntax."""
        board = divider()
        lower = cast(Resistor, board.components()[1])
        with board.check(
            "injection", ground=Nets.GROUND, purpose="forced load"
        ) as check:
            check.inject_current("ILOAD", Nets.POWER, Nets.GROUND, amperes=0.001)
            check.voltage_at(
                lower,
                ResistorPin.TERMINAL_A,
                between=(-2, 2),
                because="midpoint stays in expected range",
            )
        self.assertIn("ILOAD n1 0 DC 0.001", board.deck("injection"))
