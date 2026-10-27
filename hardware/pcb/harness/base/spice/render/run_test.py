"""Tests beside handling of ngspice process output and measured results."""

import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from pcb.harness import Limit
from pcb.harness.base.spice.render.deck_test import divider_board
from pcb.harness.base.spice.render.run import parse_output, run_deck


class RunTest(unittest.TestCase):
    def test_reads_a_valid_measured_result(self) -> None:
        output = "result_r2_0 = 1.650000e+00\nngspice done\n"
        self.assertEqual(
            parse_output(output, {"result_r2_0": Limit(1.5, 1.8)}),
            {"result_r2_0": 1.65},
        )

    def test_error_text_fails_even_when_process_exits_zero(self) -> None:
        output = "Error: no such vector\nresult_r2_0 = 1.65\n"
        with self.assertRaisesRegex(ValueError, "ngspice error"):
            parse_output(output, {"result_r2_0": Limit(1.5, 1.8)})

    def test_missing_result_fails(self) -> None:
        with self.assertRaisesRegex(ValueError, "missing result"):
            parse_output("ngspice done", {"result_r2_0": Limit(1.5, 1.8)})

    def test_out_of_window_result_fails(self) -> None:
        with self.assertRaisesRegex(ValueError, "outside"):
            parse_output("result_r2_0 = 1.2", {"result_r2_0": Limit(1.5, 1.8)})

    def test_execution_preserves_output_and_failure_evidence(self) -> None:
        board = divider_board()
        transcript = "result_r2_0 = 1.65\n"
        for persistent in (False, True):
            for status in (0, 7):
                with self.subTest(persistent=persistent, status=status):
                    paths: list[Path] = []

                    def execute(
                        command: tuple[str, str, str],
                        *,
                        paths: list[Path] = paths,
                        status: int = status,
                        **options: object,
                    ) -> subprocess.CompletedProcess[str]:
                        directory = options["cwd"]
                        self.assertIsInstance(directory, Path)
                        assert isinstance(directory, Path)
                        path = directory / command[2]
                        paths.append(path)
                        self.assertEqual(path.read_text(), board.deck("normal"))
                        self.assertEqual(command[:2], ("/mock/ngspice", "-b"))
                        self.assertEqual(
                            options,
                            {
                                "cwd": directory,
                                "check": False,
                                "capture_output": True,
                                "text": True,
                                "timeout": 30,
                            },
                        )
                        return subprocess.CompletedProcess(
                            command, status, transcript, "diagnostic\n"
                        )

                    with (
                        tempfile.TemporaryDirectory() as temporary,
                        patch("shutil.which", return_value="/mock/ngspice"),
                        patch("subprocess.run", side_effect=execute),
                    ):
                        output = (
                            Path(temporary) / "nested" / "check.cir"
                            if persistent
                            else None
                        )
                        if status:
                            with self.assertRaisesRegex(ValueError, "ngspice exited 7"):
                                run_deck(board, "normal", output=output)
                        else:
                            self.assertEqual(
                                run_deck(board, "normal", output=output),
                                {"result_r2_0": 1.65},
                            )
                        if output is not None:
                            self.assertEqual(
                                output.with_suffix(".log").read_text(),
                                transcript + "diagnostic\n",
                            )
                            self.assertEqual(paths, [output])
                        else:
                            self.assertEqual(len(paths), 1)
                            self.assertFalse(paths[0].parent.exists())
