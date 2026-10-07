"""Review persists one electrical suite; standalone check still runs it."""

import unittest
from unittest.mock import patch

from pcb.__main__ import main
from pcb.board.board import Board


class ReviewPipelineTest(unittest.TestCase):
    def test_review_leaves_electrical_suite_to_generation(self) -> None:
        board = Board()
        with (
            patch("sys.argv", ["pcb", "review"]),
            patch("pcb.__main__.Board", return_value=board),
            patch("pcb.__main__.check") as check,
            patch("pcb.__main__.generate") as generate,
        ):
            main()
            check.assert_called_once_with(board, electrical=False)
            generate.assert_called_once_with()

    def test_standalone_check_includes_electrical_suite(self) -> None:
        board = Board()
        with (
            patch("sys.argv", ["pcb", "check"]),
            patch("pcb.__main__.Board", return_value=board),
            patch("pcb.__main__.check") as check,
            patch("pcb.__main__.generate") as generate,
        ):
            main()
            check.assert_called_once_with(board, electrical=True)
            generate.assert_not_called()

    def test_failed_preliminary_check_prevents_generation(self) -> None:
        with (
            patch("sys.argv", ["pcb", "review"]),
            patch("pcb.__main__.Board"),
            patch("pcb.__main__.check", side_effect=ValueError("failed")),
            patch("pcb.__main__.generate") as generate,
            self.assertRaisesRegex(ValueError, "failed"),
        ):
            main()
        generate.assert_not_called()
