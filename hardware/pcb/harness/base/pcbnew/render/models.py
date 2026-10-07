"""Attach portable STEP bodies to every real PCB component before 3D export."""

from enum import StrEnum
from pathlib import Path
from typing import cast

import pcbnew

from pcb.board.assembly import PcbSnapshot

from ...circuit import Circuit
from ...component import BoardComponent
from ...model import Model3D
from ...net import Net


def write_step(model: Model3D, path: Path) -> None:
    import cadquery as cq

    assembly = cq.Assembly(name=path.stem)
    for solid in model.solids:
        x, y, z = solid.size_mm
        shape = (
            cq.Workplane().box(x, y, z)
            if solid.shape == "box"
            else cq.Workplane().cylinder(z, x / 2)
        ).translate(solid.center_mm)
        assembly.add(shape, name=solid.name, color=cq.Color(*solid.color))
    assembly.export(str(path))
    if not path.is_file() or path.stat().st_size == 0:
        raise RuntimeError(f"STEP export is missing: {path}")


def attach_models[BoardNet: Net](circuit: Circuit[BoardNet], board_path: Path) -> None:
    board = pcbnew.LoadBoard(str(board_path))
    directory = board_path.parent / "models"
    directory.mkdir()
    models: dict[str, Model3D] = {}
    for component in circuit.components():
        part = cast(BoardComponent[StrEnum], component)
        definition = part.definition
        key = definition.product.key
        model = definition.model_3d or Model3D.envelope(definition.product.body_mm)
        if key in models and models[key] != model:
            raise ValueError(f"{key}: conflicting component models")
        if key not in models:
            write_step(model, directory / f"{key}.step")
            models[key] = model
        footprint = board.FindFootprintByReference(part.reference)
        if footprint is None:
            raise ValueError(f"{part.reference}: missing footprint for 3D model")
        native = pcbnew.FP_3DMODEL()
        native.m_Filename = f"${{KIPRJMOD}}/models/{key}.step"
        footprint.Models().push_back(native)
    if not pcbnew.SaveBoard(str(board_path), board):
        raise OSError("KiCad could not save attached component models")


def record_export[BoardNet: Net](
    circuit: Circuit[BoardNet],
    board_path: Path,
    glb_path: Path,
    snapshot: PcbSnapshot,
    source_fingerprint: str,
) -> None:
    import json

    from ..model_export import (
        check_component_coverage,
        file_digest,
        toolchain_versions,
    )

    parts = tuple(cast(BoardComponent[StrEnum], part) for part in circuit.components())
    snapshot_path = board_path.parent / "pcb-components.json"
    snapshot.write(snapshot_path)
    check_component_coverage(glb_path, {part.reference for part in parts})
    report = {
        "source_digest": source_fingerprint,
        "toolchain": toolchain_versions(),
        "pcb_sha256": file_digest(board_path),
        "glb_sha256": file_digest(glb_path),
        "snapshot_sha256": file_digest(snapshot_path),
        "components": {
            part.reference: {
                "model": f"models/{part.definition.product.key}.step",
                "fidelity": (
                    part.definition.model_3d
                    or Model3D.envelope(part.definition.product.body_mm)
                ).fidelity,
            }
            for part in parts
        },
    }
    (board_path.parent / "3d-models.json").write_text(
        json.dumps(report, indent=2) + "\n"
    )
