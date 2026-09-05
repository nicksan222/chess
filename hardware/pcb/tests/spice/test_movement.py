"""Movement scenarios against the native board connectivity."""

from __future__ import annotations

import unittest

from spice.movement import MovementCase
from spice.support import board_circuits, run_circuit


class MovementSpiceTest(unittest.TestCase):
    def test_lift_then_place_is_electrically_visible(self) -> None:
        case = (
            MovementCase("quiet")
            .starts_with("A2")
            .expect_occupied("origin_before_lift", "A2", at_ms=0.25)
            .expect_empty("target_before_move", "A4", at_ms=0.25)
            .lift("A2", at_ms=1)
            .expect_empty("origin_after_lift", "A2", at_ms=1.25)
            .place("A4", at_ms=2)
            .expect_occupied("target_after_place", "A4", at_ms=2.25)
        )
        circuit = board_circuits().movement(case)
        run_circuit("test_move_quiet.py", circuit)

    def test_captured_piece_and_attacker_transitions_are_visible(self) -> None:
        case = (
            MovementCase("capture")
            .starts_with("E4", "D5")
            .expect_occupied("attacker_initial", "E4", at_ms=0.25)
            .expect_occupied("victim_initial", "D5", at_ms=0.25)
            .lift("D5", at_ms=1)
            .expect_empty("victim_removed", "D5", at_ms=1.25)
            .lift("E4", at_ms=2)
            .expect_empty("attacker_lifted", "E4", at_ms=2.25)
            .place("D5", at_ms=3)
            .expect_occupied("attacker_placed", "D5", at_ms=3.25)
        )
        circuit = board_circuits().movement(case)
        run_circuit("test_move_capture.py", circuit)

    def test_king_and_rook_transitions_are_visible(self) -> None:
        case = (
            MovementCase("castle")
            .starts_with("E1", "H1")
            .expect_occupied("king_initial", "E1", at_ms=0.25)
            .expect_occupied("rook_initial", "H1", at_ms=0.25)
            .expect_empty("king_destination_initial", "G1", at_ms=0.25)
            .expect_empty("rook_destination_initial", "F1", at_ms=0.25)
            .lift("E1", at_ms=1)
            .expect_empty("king_lifted", "E1", at_ms=1.25)
            .place("G1", at_ms=2)
            .expect_occupied("king_placed", "G1", at_ms=2.25)
            .lift("H1", at_ms=3)
            .expect_empty("rook_lifted", "H1", at_ms=3.25)
            .place("F1", at_ms=4)
            .expect_occupied("rook_placed", "F1", at_ms=4.25)
        )
        circuit = board_circuits().movement(case)
        run_circuit("test_move_castle.py", circuit)

    def test_three_square_transition_is_visible(self) -> None:
        case = (
            MovementCase("en-passant")
            .starts_with("E5", "D5")
            .expect_occupied("attacker_initial", "E5", at_ms=0.25)
            .expect_occupied("victim_initial", "D5", at_ms=0.25)
            .expect_empty("destination_initial", "D6", at_ms=0.25)
            .lift("E5", at_ms=1)
            .expect_empty("attacker_lifted", "E5", at_ms=1.25)
            .lift("D5", at_ms=2)
            .expect_empty("victim_removed", "D5", at_ms=2.25)
            .place("D6", at_ms=3)
            .expect_occupied("destination_filled", "D6", at_ms=3.25)
        )
        circuit = board_circuits().movement(case)
        run_circuit("test_move_en_passant.py", circuit)

    def test_promotion_rank_transition_is_visible(self) -> None:
        case = (
            MovementCase("promotion")
            .starts_with("A7")
            .expect_occupied("pawn_initial", "A7", at_ms=0.25)
            .expect_empty("promotion_square_initial", "A8", at_ms=0.25)
            .lift("A7", at_ms=1)
            .expect_empty("pawn_lifted", "A7", at_ms=1.25)
            .place("A8", at_ms=2)
            .expect_occupied("promoted_piece_placed", "A8", at_ms=2.25)
        )
        circuit = board_circuits().movement(case)
        run_circuit("test_move_promotion.py", circuit)
