"""The exported KiCad assembly, imported without rebuilding its geometry."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from cad.harness.base.component import Component
from cad.harness.base.pcb import PcbSnapshot

if TYPE_CHECKING:
    import bpy


class PcbAssembly(Component):
    fit_check = True

    def __init__(self, source: Path, snapshot: PcbSnapshot) -> None:
        super().__init__("PCB_Assembly")
        self.source = source
        self.snapshot = snapshot

    def build(
        self,
        collection: bpy.types.Collection,
        construction: bpy.types.Collection,
        palette: dict[str, bpy.types.Material],
    ) -> tuple[bpy.types.Object, ...]:
        from cad.harness.base.blender.pcb_import import import_board

        return (import_board(self.source, self.snapshot, self.reference, collection),)
