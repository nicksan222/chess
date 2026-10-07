"""Run a generated deck and refuse missing or failed electrical evidence."""

from __future__ import annotations

import re
import shutil
import subprocess
import tempfile
from pathlib import Path

from ...registry import BoardRegistry
from ..measurement import Limit
from .deck import render_deck
from .number import spice_number


def parse_output(output: str, expected: dict[str, Limit]) -> dict[str, float]:
    """Read scalar results, checking process text and every declared limit.

    ngspice may report a failed measurement yet still exit with status zero.
    The output is therefore checked for its own error markers and for every
    expected result before any pass is reported. This is independent of the
    pass/fail commands embedded in the deck.
    """
    if re.search(r"(?im)^\s*Error:|failed!|simulation\(s\) aborted", output):
        raise ValueError(f"ngspice error:\n{output}")
    found: dict[str, float] = {}
    for match in re.finditer(r"(?m)^\s*(result_[a-z0-9_]+)\s*=\s*([^\s]+)", output):
        name, value = match.group(1), match.group(2)
        try:
            found[name] = float(value)
        except ValueError as error:
            raise ValueError(f"nonnumeric SPICE result {name}: {value}") from error
    for name, limit in expected.items():
        if name not in found:
            raise ValueError(f"missing result from ngspice: {name}")
        if not limit.minimum <= found[name] <= limit.maximum:
            raise ValueError(
                f"{name}={spice_number(found[name])} outside "
                f"[{spice_number(limit.minimum)}, {spice_number(limit.maximum)}]"
            )
    return {name: found[name] for name in expected}


def run_deck(
    board: BoardRegistry,
    scenario_name: str,
    executable: str = "ngspice",
    *,
    output: Path | None = None,
) -> dict[str, float]:
    """Render, execute and check one scenario using an installed ngspice binary.

    The temporary circuit file disappears after the process finishes. A missing
    executable, nonzero exit, ngspice error text, missing result or failed limit
    is an error. This function does not claim physical board validation.
    """
    resolved = shutil.which(executable)
    if resolved is None:
        raise RuntimeError(f"{executable} is required to run SPICE scenarios")
    deck = render_deck(board, scenario_name)
    names = re.findall(r"(?m)^print (result_[a-z0-9_]+)$", deck)
    requirements = [
        requirement.allowed
        for _, requirement in board.spice_requirements()
        if requirement.scenario == scenario_name
    ]
    if len(names) != len(requirements):
        raise ValueError("rendered result count differs from SPICE requirements")
    expected = dict(zip(names, requirements, strict=True))
    if output is not None:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(deck)
        process = subprocess.run(
            (resolved, "-b", output.name),
            cwd=output.parent,
            check=False,
            capture_output=True,
            text=True,
            timeout=30,
        )
        transcript = process.stdout + process.stderr
        output.with_suffix(".log").write_text(transcript)
        if process.returncode != 0:
            raise ValueError(f"ngspice exited {process.returncode}:\n{transcript}")
        return parse_output(transcript, expected)
    with tempfile.TemporaryDirectory(prefix="chess-harness-spice-") as directory:
        path = Path(directory) / "scenario.cir"
        path.write_text(deck)
        process = subprocess.run(
            (resolved, "-b", path.name),
            cwd=path.parent,
            check=False,
            capture_output=True,
            text=True,
            timeout=30,
        )
    transcript = process.stdout + process.stderr
    if process.returncode != 0:
        raise ValueError(f"ngspice exited {process.returncode}:\n{transcript}")
    return parse_output(transcript, expected)
