"""Rear rocker housing, face, terminals and insulated receptacle envelopes."""

from __future__ import annotations

from typing import TYPE_CHECKING

from cad.harness.base.component import Component
from shared import dimensions as d
from shared.dimensions import rear_panel as rear

if TYPE_CHECKING:
    import bpy


class PanelPowerSwitch(Component):
    fit_check = True
    product_key = "POWER_SWITCH"

    def __init__(self) -> None:
        super().__init__(self.product_key)

    @property
    def object_names(self) -> tuple[str, ...]:
        return tuple(
            f"{self.reference}_{name}"
            for name in (
                "Body",
                "Face",
                "Terminal1",
                "Terminal2",
            )
        )

    def build(
        self,
        collection: bpy.types.Collection,
        construction: bpy.types.Collection,
        palette: dict[str, bpy.types.Material],
    ) -> tuple[bpy.types.Object, ...]:
        from cad.harness.base.blender import modeling

        x, z = d.CASE_ROCKER_APERTURE_CENTER_X_MM, d.CASE_REAR_APERTURE_CENTER_Z_MM
        y = rear.REAR_PANEL_Y_MM
        body_end = y - rear.ROCKER_BODY_MM[1]
        tabs_end = body_end - rear.ROCKER_TERMINAL_LENGTH_MM
        specs = [
            ("Body", rear.ROCKER_BODY_MM, (x, y - rear.ROCKER_BODY_MM[1] / 2, z)),
            ("Face", rear.ROCKER_FACE_MM, (x, y + rear.ROCKER_FACE_MM[1] / 2, z)),
        ]
        for i, sign in enumerate((-1, 1), 1):
            cx = x + sign * rear.ROCKER_TERMINAL_PITCH_MM / 2
            specs.append(
                (
                    f"Terminal{i}",
                    (
                        rear.ROCKER_TERMINAL_WIDTH_MM,
                        rear.ROCKER_TERMINAL_LENGTH_MM,
                        rear.ROCKER_TERMINAL_THICKNESS_MM,
                    ),
                    (cx, (body_end + tabs_end) / 2, z),
                )
            )
        objects: list[bpy.types.Object] = []
        for name, size, center in specs:
            part = modeling.rounded_box(
                f"{self.reference}_{name}", size, center, 0.2, collection
            )
            part.data.materials.append(palette["body"])
            part["physical_reference"] = self.reference
            part["fidelity"] = (
                "datasheet body; simplified actuator and terminal envelopes"
            )
            objects.append(part)
        return tuple(objects)
