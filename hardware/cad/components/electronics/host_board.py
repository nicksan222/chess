"""Raspberry Pi Zero 2 W; the host processor."""

from __future__ import annotations

from typing import TYPE_CHECKING

from cad.harness.base.component import Component
from shared import dimensions

if TYPE_CHECKING:
    import bpy


class HostBoard(Component):
    fit_check = True

    def __init__(self) -> None:
        super().__init__("Proxy_Host_Board")

    def build(
        self,
        collection: bpy.types.Collection,
        construction: bpy.types.Collection,
        palette: dict[str, bpy.types.Material],
    ) -> tuple[bpy.types.Object, ...]:
        from cad.harness.base.blender import modeling

        length, width, thickness = dimensions.PI_BOARD_SIZE_MM
        turned = int(dimensions.PI_ROTATION_DEG) % 180 == 90
        part = modeling.rounded_box(
            self.reference,
            (width, length, thickness) if turned else (length, width, thickness),
            (*dimensions.PI_CENTER_MM, dimensions.PI_TOP_FACE_Z_MM - thickness / 2),
            0.5,
            collection,
        )
        part.data.materials.append(palette["host"])
        part["purpose"] = "Raspberry Pi Zero 2 W; the host processor"
        return (part,)
