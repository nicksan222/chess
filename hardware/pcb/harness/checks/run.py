"""Validate the new board, its component catalog and the reusable harness."""

import os
import subprocess
import sys
from pathlib import Path
from tempfile import TemporaryDirectory

from pcb.harness import Circuit, Net
from pcb.harness.base.spice.render.suite import run_suite

PCB_ROOT = Path(__file__).resolve().parents[2]


def check[BoardNet: Net](
    declaration: Circuit[BoardNet], *, electrical: bool = True
) -> None:
    declaration.validate()
    for command in (
        ("ruff", "check", str(PCB_ROOT)),
        ("ruff", "format", "--check", str(PCB_ROOT)),
        (
            os.environ.get("BASEDPYRIGHT", "basedpyright"),
            "--project",
            str(PCB_ROOT / "pyrightconfig.json"),
        ),
    ):
        subprocess.run(command, check=True)
    for directory, pattern in (
        (PCB_ROOT / "harness", "*_test.py"),
        (PCB_ROOT / "components", "*_test.py"),
        (PCB_ROOT / "harness/checks", "test_*.py"),
    ):
        subprocess.run(
            (
                sys.executable,
                "-m",
                "unittest",
                "discover",
                "-s",
                str(directory),
                "-t",
                str(PCB_ROOT.parent),
                "-p",
                pattern,
            ),
            check=True,
        )
    if not electrical:
        return
    with TemporaryDirectory(prefix="pcb-board-tests-") as temporary:
        result = run_suite(PCB_ROOT / "board/tests", Path(temporary))
        if result["complete"] is not True:
            raise ValueError("board electrical checks are incomplete")
        print(f"Board pytest checks: {result['passed']} passed")
