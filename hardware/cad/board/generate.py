"""One entry point for the CAD models, assembly and review renders.

Run: PYTHONPATH=hardware python3 -m cad.board.generate /opt/blender/blender.
The same file acts as Blender's worker when given an output directory after --.
"""

from __future__ import annotations

import argparse
import json
import platform
import sys
from pathlib import Path

# Blender does not inherit PYTHONPATH unless explicitly configured.
HARDWARE_ROOT = Path(__file__).resolve().parents[2]
if str(HARDWARE_ROOT) not in sys.path:
    sys.path.insert(0, str(HARDWARE_ROOT))

from cad.board.board import Board
from cad.harness.base.generation import publish
from cad.harness.base.pcb import PcbSnapshot
from cad.harness.checks.clearance import bottom_side_violations, top_side_violations
from shared import dimensions

GENERATED = Path(__file__).resolve().parents[1] / "generated"


def generate(blender: Path, destination: Path = GENERATED) -> None:
    from cad.harness.base.pcb_export import prepare_export

    publish(
        blender,
        Path(__file__).resolve(),
        destination,
        prepare=prepare_export,
    )


def render(output: Path) -> None:
    import bpy

    from cad.harness.base.blender.render import render_assembly, render_printable
    from cad.harness.base.blender.testing import run_tests

    board = Board(
        PcbSnapshot.read(output / "pcb-components.json"), output / "chess-board.glb"
    )
    dimensions.validate()
    for check in (top_side_violations, bottom_side_violations):
        if violations := check(board.pcb_definition):
            raise RuntimeError(f"PCB components do not fit the assembly: {violations}")
    # Build and validate every owning model, then assemble their exact saved meshes.
    printed = [render_printable(part, output) for part in board.printable_components()]
    assembly = render_assembly(board.case, board.plate, board.electronics, output)
    assembly_path = output / "board-assembly.blend"
    bpy.ops.wm.open_mainfile(filepath=str(assembly_path))
    if Path(bpy.data.filepath).resolve() != assembly_path.resolve():
        raise RuntimeError(
            "Saved assembly could not be reopened for native verification"
        )
    native_tests = run_tests(Path(__file__).resolve().parent / "tests" / "blender")
    outputs = [
        *(
            f"{part.output_name}.{extension}"
            for part in board.printable_components()
            for extension in ("blend", "png")
        ),
        "pcb-components.json",
        "chess-board.glb",
        "3d-models.json",
        "board-assembly.blend",
        "board-assembly-finished.png",
        "board-assembly-open.png",
    ]
    manifest: dict[str, object] = {
        "checks_passed": True,
        "pcb_geometry_source": "chess-board.glb",
        "pcb_geometry_rebuilt": False,
        "pcb_model_report": "3d-models.json",
        "native_board_tests": native_tests,
        "native_tests_reopened_artifact": assembly_path.name,
        "blender_runtime": {
            "version": bpy.app.version_string,
            "build_hash": bpy.app.build_hash.decode(),
            "version_cycle": bpy.app.version_cycle,
            "python_version": platform.python_version(),
        },
        "components": len(board.components()),
        "pcb_components": len(board.pcb_parts),
        "printed_parts": printed,
        "assembly": assembly,
        "outputs": outputs,
        "manufacturing_approved": False,
        "remaining": "Calibrated print, material shrinkage and physical clearance verification remain pending.",
    }
    (output / "README.md").write_text(
        "# Generated CAD\n\nSource: `cad.board.board.Board()`. Regenerate with "
        "`just --justfile hardware/cad/justfile generate`.\n\n"
        "Owning case, plate and button-cap models and their exact assembled meshes; PCB geometry "
        "is imported from KiCad’s checked `chess-board.glb` export. `manifest.json` records mesh and fit checks. "
        "Electronic bodies are envelopes, not detailed supplier models. These checks do not "
        "prove physical fit, shrinkage or manufacturing approval.\n"
    )

    from cad.harness.base.provenance import record_provenance

    outputs.append("README.md")
    record_provenance(output, manifest)
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")


if __name__ == "__main__":
    if "--" in sys.argv:
        arguments = sys.argv[sys.argv.index("--") + 1 :]
        if len(arguments) != 1:
            raise RuntimeError("Blender worker expects one output directory")
        render(Path(arguments[0]).resolve())
    else:
        parser = argparse.ArgumentParser(description=__doc__)
        parser.add_argument("blender", type=Path)

        class Options(argparse.Namespace):
            blender: Path = Path("/opt/blender/blender")

        options = parser.parse_args(namespace=Options())
        generate(options.blender)
