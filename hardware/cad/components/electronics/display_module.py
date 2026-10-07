"""Layered MC242GW module behind the owning plate's display bezel."""

from __future__ import annotations

from typing import TYPE_CHECKING

from cad.harness.base.component import Component
from shared import dimensions as d

if TYPE_CHECKING:
    import bpy


class DisplayModule(Component):
    fit_check = True

    def __init__(self) -> None:
        super().__init__("Proxy_Display_Module")

    @property
    def object_names(self) -> tuple[str, ...]:
        return (
            self.reference,
            f"{self.reference}_Underside",
            f"{self.reference}_Frame",
            f"{self.reference}_Screen",
        )

    def build(
        self,
        collection: bpy.types.Collection,
        construction: bpy.types.Collection,
        palette: dict[str, bpy.types.Material],
    ) -> tuple[bpy.types.Object, ...]:
        from cad.harness.base.blender import modeling

        x, y = d.PANEL_OLED_CENTER_MM
        width, height, _ = d.PANEL_OLED_MODULE_MM
        pcb_z = d.PANEL_OLED_PCB_BOTTOM_Z_MM
        pcb_top = pcb_z + d.PANEL_OLED_PCB_THICKNESS_MM
        specs = (
            (
                self.reference,
                (width, height, d.PANEL_OLED_PCB_THICKNESS_MM),
                (x, y, pcb_z + d.PANEL_OLED_PCB_THICKNESS_MM / 2),
                "pcb",
            ),
            (
                self.object_names[1],
                d.PANEL_OLED_UNDERSIDE_SIZE_MM,
                (x, y, pcb_z - d.PANEL_OLED_UNDERSIDE_HEIGHT_MM / 2),
                "body",
            ),
            (
                self.object_names[2],
                d.PANEL_OLED_FRAME_MM,
                (x, y, pcb_top + d.PANEL_OLED_FRAME_MM[2] / 2),
                "body",
            ),
            (
                self.object_names[3],
                (*d.PANEL_OLED_SCREEN_SIZE_MM, 0.02),
                (
                    x + d.PANEL_OLED_SCREEN_OFFSET_MM[0],
                    y + d.PANEL_OLED_SCREEN_OFFSET_MM[1],
                    d.PANEL_OLED_SCREEN_Z_MM - 0.01,
                ),
                "display",
            ),
        )
        objects: list[bpy.types.Object] = []
        for name, size, center, material in specs:
            obj = modeling.rounded_box(name, size, center, 0, collection)
            obj.data.materials.append(palette[material])
            obj["physical_reference"] = self.reference
            obj["fidelity"] = (
                "supplier-dimension envelopes; upright header omitted for direct soldering"
            )
            objects.append(obj)
        modeling.cut_batch(
            objects[0],
            [
                modeling.cylinder_between(
                    f"Module_mount_hole_{i}",
                    d.PANEL_OLED_MOUNT_HOLE_DIAMETER_MM,
                    (x + dx, y + dy),
                    pcb_z - 0.2,
                    pcb_top + 0.2,
                    construction,
                    vertices=24,
                )
                for i, (dx, dy) in enumerate(d.PANEL_OLED_MOUNT_HOLES_MM)
            ],
            "Module mounting holes",
        )
        # The OLED face occupies a real pocket in the carrier frame.
        screen = objects[-1]
        cutter = modeling.rounded_box(
            "Screen frame pocket",
            (*d.PANEL_OLED_SCREEN_SIZE_MM, 0.06),
            (screen.location.x, screen.location.y, screen.location.z),
            0,
            construction,
        )
        modeling.cut_batch(objects[-2], [cutter], "Frame screen pocket")
        return tuple(objects)
