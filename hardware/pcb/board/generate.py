"""Generate the chess board project and review outputs from its new circuit.

Run: PYTHONPATH=hardware python3 -m pcb.board.generate.
The harness owns conversion and checks; this file states their execution order.
"""

from __future__ import annotations

import argparse
import subprocess
from pathlib import Path

from build_support import staged_output

from pcb.board.board import Board
from pcb.harness.base.pcbnew.design_rules import write_rules
from pcb.harness.base.pcbnew.render.bom import write_bom
from pcb.harness.base.pcbnew.render.connections import write_connections
from pcb.harness.base.pcbnew.render.fabrication import write_fabrication
from pcb.harness.base.pcbnew.render.fill import fill_planes
from pcb.harness.base.pcbnew.render.preview import prepare_svg
from pcb.harness.base.pcbnew.render.project import write_schematic_project
from pcb.harness.base.pcbnew.render.report import write_report
from pcb.harness.base.spice.render.suite import run_suite
from pcb.harness.checks.pcbnew.netlist import apply_netlist
from pcb.harness.checks.pcbnew.reports import (
    check_routed_copper,
    check_schematic_parity,
)

GENERATED = Path(__file__).resolve().parents[1] / "generated"
NAME = "chess-board"


def run(directory: Path, *arguments: str) -> None:
    """Fail on tool errors; append diagnostics to the staged generation log."""
    result = subprocess.run(
        arguments, capture_output=True, text=True, check=False, timeout=120
    )
    with (directory / "generation.log").open("a") as log:
        log.write(" ".join(arguments) + "\n" + result.stdout + result.stderr)
    if result.returncode:
        raise RuntimeError(f"{arguments[0]} failed: {result.stdout}{result.stderr}")


def generate(destination: Path = GENERATED) -> Path:
    """Publish the complete export set, preserving previous output on failure."""
    declaration = Board()
    declaration.route()
    with staged_output(destination) as stage:
        write_schematic_project(declaration, stage, NAME)
        electrical_checks = run_suite(
            Path(__file__).resolve().parent / "tests", stage / "electrical-checks"
        )
        if electrical_checks["complete"] is not True:
            raise ValueError("board electrical checks are incomplete")
        write_bom(declaration, stage / "bom.csv")
        board_path = stage / f"{NAME}.kicad_pcb"
        schematic_path = stage / f"{NAME}.kicad_sch"
        netlist_path = stage / "netlist.xml"
        run(
            stage,
            "kicad-cli",
            "sch",
            "export",
            "netlist",
            "--format",
            "kicadxml",
            "-o",
            str(netlist_path),
            str(schematic_path),
        )
        apply_netlist(declaration, netlist_path, board_path, stage / "netlist.json")
        write_rules(declaration, declaration.design_rules, stage, NAME)
        fill_planes(board_path)
        write_connections(declaration, board_path, stage / "board-connections.svg")
        run(
            stage,
            "kicad-cli",
            "sch",
            "erc",
            "--format",
            "json",
            "--severity-all",
            "-o",
            str(stage / "erc.json"),
            str(schematic_path),
        )
        run(
            stage,
            "kicad-cli",
            "pcb",
            "drc",
            "--format",
            "json",
            "--severity-all",
            "--schematic-parity",
            "-o",
            str(stage / "drc.json"),
            str(board_path),
        )
        check_schematic_parity(stage / "drc.json")
        check_routed_copper(stage / "drc.json")
        run(
            stage,
            "kicad-cli",
            "sch",
            "export",
            "pdf",
            "-o",
            str(stage / "schematic.pdf"),
            str(schematic_path),
        )
        run(
            stage,
            "kicad-cli",
            "sch",
            "export",
            "svg",
            "-o",
            str(stage / "schematic"),
            str(schematic_path),
        )
        run(
            stage,
            "kicad-cli",
            "pcb",
            "export",
            "svg",
            "--mode-single",
            "--page-size-mode",
            "2",
            "--fit-page-to-board",
            "--exclude-drawing-sheet",
            "--layers",
            "F.Cu,F.SilkS,F.Fab,Edge.Cuts",
            "-o",
            str(stage / "board-top.svg"),
            str(board_path),
        )
        run(
            stage,
            "kicad-cli",
            "pcb",
            "export",
            "svg",
            "--mode-single",
            "--page-size-mode",
            "2",
            "--fit-page-to-board",
            "--exclude-drawing-sheet",
            "--mirror",
            "--layers",
            "B.Cu,B.SilkS,B.Fab,Edge.Cuts",
            "-o",
            str(stage / "board-bottom.svg"),
            str(board_path),
        )
        run(
            stage,
            "kicad-cli",
            "pcb",
            "export",
            "svg",
            "--mode-single",
            "--page-size-mode",
            "2",
            "--fit-page-to-board",
            "--exclude-drawing-sheet",
            "--layers",
            "F.Cu,B.Cu,In4.Cu,In5.Cu,F.SilkS,Edge.Cuts",
            "-o",
            str(stage / "board-routing.svg"),
            str(board_path),
        )
        for side in ("top", "bottom", "routing"):
            prepare_svg(stage / f"board-{side}.svg", side)
            run(
                stage,
                "rsvg-convert",
                "--width",
                "1600",
                "-o",
                str(stage / f"board-{side}.png"),
                str(stage / f"board-{side}.svg"),
            )
        run(
            stage,
            "kicad-cli",
            "pcb",
            "render",
            "--rotate",
            "-35,0,25",
            "-o",
            str(stage / "board-3d.png"),
            str(board_path),
        )
        run(
            stage,
            "kicad-cli",
            "pcb",
            "export",
            "pos",
            "--format",
            "csv",
            "--units",
            "mm",
            "-o",
            str(stage / "positions.csv"),
            str(board_path),
        )
        write_fabrication(
            declaration, board_path, stage, NAME, declaration.fabrication_pending, run
        )
        write_report(
            declaration, stage, NAME, declaration.fabrication_pending, electrical_checks
        )
    return destination / f"{NAME}.kicad_pro"


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=GENERATED)

    class Options(argparse.Namespace):
        output: Path = GENERATED

    options = parser.parse_args(namespace=Options())
    print(generate(options.output))
