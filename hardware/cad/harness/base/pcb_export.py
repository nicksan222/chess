"""Consume one coherent checked PCB assembly export before building CAD."""

import json
import shutil
from pathlib import Path
from typing import cast

from pcb.harness.base.pcbnew.model_export import (
    check_component_coverage,
    file_digest,
    source_digest,
)

from .pcb import PcbSnapshot

SOURCE = Path(__file__).resolve().parents[3] / "pcb" / "generated"
EXPORT_FILES = (
    "chess-board.glb",
    "3d-models.json",
    "pcb-components.json",
    "chess-board.kicad_pcb",
)


def pcb_bundle_current(directory: Path, snapshot: PcbSnapshot | None = None) -> bool:
    try:
        raw = cast(object, json.loads((directory / "3d-models.json").read_text()))
        if not isinstance(raw, dict):
            return False
        report = cast(dict[str, object], raw)
        if (
            report["source_digest"] != source_digest()
            or report["glb_sha256"] != file_digest(directory / "chess-board.glb")
            or report["snapshot_sha256"]
            != file_digest(directory / "pcb-components.json")
        ):
            return False
        exported = PcbSnapshot.read(directory / "pcb-components.json")
        if snapshot is not None and snapshot != exported:
            return False
        check_component_coverage(
            directory / "chess-board.glb", {part.reference for part in exported.parts}
        )
    except (OSError, ValueError, KeyError, TypeError, AttributeError):
        return False
    return True


def export_current(directory: Path, snapshot: PcbSnapshot | None = None) -> bool:
    if not pcb_bundle_current(directory, snapshot):
        return False
    try:
        report = cast(
            dict[str, object], json.loads((directory / "3d-models.json").read_text())
        )
        return report["pcb_sha256"] == file_digest(directory / "chess-board.kicad_pcb")
    except (OSError, ValueError, KeyError, TypeError):
        return False


def prepare_export(stage: Path, snapshot: PcbSnapshot | None = None) -> None:
    if not export_current(SOURCE, snapshot):
        from pcb.board.generate import generate

        print("CAD: regenerating the PCB export from current definitions", flush=True)
        generate()
    # Publication may swap SOURCE during the copy. Validate the copy itself;
    # retry once rather than accepting files from different generations.
    for _ in range(2):
        try:
            for name in EXPORT_FILES:
                shutil.copyfile(SOURCE / name, stage / name)
        except OSError:
            continue
        if export_current(stage, snapshot):
            (stage / "chess-board.kicad_pcb").unlink()
            return
    raise RuntimeError(
        "PCB assembly export is incomplete, stale or changed during copying"
    )
