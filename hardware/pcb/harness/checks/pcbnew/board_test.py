"""Negative controls prove native checks detect damaged rendered boards."""

import unittest
from typing import cast

import pcbnew

from pcb.harness import BoardComponent, BoardOutline, Circuit, NoConnect, Placement
from pcb.harness.base.pcbnew.render.board import render_board
from pcb.harness.base.pcbnew.render.board_test import Nets, Pin, sample_board

from .board import validate_board


class NativeBoardChecksTest(unittest.TestCase):
    def test_unchanged_registry_and_native_board_pass(self) -> None:
        circuit = sample_board()
        validate_board(circuit, render_board(circuit))

    def test_missing_footprint_is_rejected(self) -> None:
        circuit = sample_board()
        board = render_board(circuit)
        board.Remove(next(iter(board.GetFootprints())))
        with self.assertRaisesRegex(ValueError, "footprints.*exactly"):
            validate_board(circuit, board)

    def test_extra_or_duplicate_footprint_is_rejected(self) -> None:
        for reference in ("U1", "EXTRA"):
            with self.subTest(reference=reference):
                circuit = sample_board()
                board = render_board(circuit)
                extra = next(iter(board.GetFootprints())).Duplicate()
                extra.SetReference(reference)
                board.Add(extra)
                with self.assertRaisesRegex(ValueError, "footprints.*exactly"):
                    validate_board(circuit, board)

    def test_missing_or_duplicate_pad_number_is_rejected(self) -> None:
        for number in ("unexpected", "1"):
            with self.subTest(number=number):
                circuit = sample_board()
                board = render_board(circuit)
                pads = {
                    pad.GetNumber(): pad
                    for pad in next(iter(board.GetFootprints())).Pads()
                }
                pads["2"].SetNumber(number)
                with self.assertRaisesRegex(ValueError, "pad coverage"):
                    validate_board(circuit, board)

    def test_pad_assigned_to_another_existing_net_is_rejected(self) -> None:
        circuit = sample_board()
        board = render_board(circuit)
        pads = list(next(iter(board.GetFootprints())).Pads())
        pads[0].SetNet(pads[1].GetNet())
        with self.assertRaisesRegex(ValueError, "wrong or missing net"):
            validate_board(circuit, board)

    def test_courtyard_on_wrong_side_is_rejected(self) -> None:
        circuit = sample_board()
        board = render_board(circuit)
        for edge in next(iter(board.GetFootprints())).GraphicalItems():
            edge.SetLayer(pcbnew.B_CrtYd)
        with self.assertRaisesRegex(ValueError, "four line segments"):
            validate_board(circuit, board)

    def test_crossed_courtyard_with_paired_endpoints_is_rejected(self) -> None:
        circuit = sample_board()
        board = render_board(circuit)
        edges = list(next(iter(board.GetFootprints())).GraphicalItems())
        points = [(edge.GetStart().x, edge.GetStart().y) for edge in edges]
        # A bow tie is closed and has four corners, but crosses itself.
        points = [points[0], points[2], points[1], points[3]]
        for edge, start, end in zip(edges, points, points[1:] + points[:1]):
            edge.SetStart(pcbnew.VECTOR2I(*start))
            edge.SetEnd(pcbnew.VECTOR2I(*end))
        with self.assertRaisesRegex(ValueError, "crossed or disconnected"):
            validate_board(circuit, board)

    def test_closed_courtyard_of_wrong_size_is_rejected(self) -> None:
        circuit = sample_board()
        board = render_board(circuit)
        footprint = next(iter(board.GetFootprints()))
        centre = footprint.GetPosition()
        for edge in footprint.GraphicalItems():
            for getter, setter in (
                (edge.GetStart, edge.SetStart),
                (edge.GetEnd, edge.SetEnd),
            ):
                point = getter()
                setter(
                    pcbnew.VECTOR2I(
                        centre.x + 2 * (point.x - centre.x),
                        centre.y + 2 * (point.y - centre.y),
                    )
                )
        with self.assertRaisesRegex(ValueError, "courtyard differs"):
            validate_board(circuit, board)

    def test_unassigned_pad_is_rejected(self) -> None:
        circuit = sample_board()
        board = render_board(circuit)
        footprint = next(iter(board.GetFootprints()))
        next(iter(footprint.Pads())).SetNet(pcbnew.NETINFO_ITEM(board, "", 0))
        with self.assertRaisesRegex(ValueError, "missing net"):
            validate_board(circuit, board)

    def test_explained_no_connect_passes_but_accidental_net_is_rejected(self) -> None:
        fixture = cast(BoardComponent[Pin], sample_board().components()[0])
        circuit = Circuit(Nets, outline=BoardOutline(20, 10))
        circuit.place(
            BoardComponent,
            reference="U1",
            definition=fixture.definition,
            placement=Placement(0, 0),
            purpose="unused pin fixture",
            pins={Pin.A: Nets.POWER, Pin.B: NoConnect("unused test contact")},
        )
        board = render_board(circuit)
        validate_board(circuit, board)
        pads = {
            pad.GetNumber(): pad for pad in next(iter(board.GetFootprints())).Pads()
        }
        self.assertEqual(pads["2"].GetNetname(), "")
        pads["2"].SetNet(pads["1"].GetNet())
        with self.assertRaisesRegex(ValueError, "wrong or missing net"):
            validate_board(circuit, board)

    def test_pad_without_copper_is_rejected(self) -> None:
        circuit = sample_board()
        board = render_board(circuit)
        pad = next(iter(next(iter(board.GetFootprints())).Pads()))
        pad.SetSize(pcbnew.VECTOR2I(0, 0))
        with self.assertRaisesRegex(ValueError, "no copper"):
            validate_board(circuit, board)

    def test_pad_outside_courtyard_is_rejected(self) -> None:
        circuit = sample_board()
        board = render_board(circuit)
        pad = next(iter(next(iter(board.GetFootprints())).Pads()))
        position = pad.GetPosition()
        pad.SetPosition(pcbnew.VECTOR2I(position.x + pcbnew.FromMM(10), position.y))
        with self.assertRaisesRegex(ValueError, "exceeds courtyard"):
            validate_board(circuit, board)

    def test_open_courtyard_is_rejected(self) -> None:
        circuit = sample_board()
        board = render_board(circuit)
        edge = next(iter(next(iter(board.GetFootprints())).GraphicalItems()))
        edge.SetEnd(pcbnew.VECTOR2I(0, 0))
        with self.assertRaisesRegex(ValueError, "not closed"):
            validate_board(circuit, board)
