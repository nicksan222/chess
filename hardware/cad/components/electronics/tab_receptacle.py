"""One purchased insulated receptacle on a rocker terminal."""

from __future__ import annotations

from typing import TYPE_CHECKING

from cad.harness.base.component import Component
from shared import dimensions as d
from shared.dimensions import rear_panel as rear

if TYPE_CHECKING:
    import bpy


class TabReceptacle(Component):
    fit_check = True
    product_key = "ROCKER_RECEPTACLE"

    def __init__(self, terminal: int) -> None:
        if terminal not in (1, 2):
            raise ValueError("Rocker receptacles attach to terminal 1 or 2")
        super().__init__(f"{self.product_key}_{terminal}")
        self.terminal = terminal

    def build(
        self,
        collection: bpy.types.Collection,
        construction: bpy.types.Collection,
        palette: dict[str, bpy.types.Material],
    ) -> tuple[bpy.types.Object, ...]:
        from cad.harness.base.blender import modeling

        size = rear.ROCKER_RECEPTACLE_MM
        obj = modeling.rounded_box(
            self.reference,
            size,
            (
                d.CASE_ROCKER_APERTURE_CENTER_X_MM
                + (self.terminal * 2 - 3) * rear.ROCKER_TERMINAL_PITCH_MM / 2,
                rear.REAR_PANEL_Y_MM
                - rear.ROCKER_BODY_MM[1]
                - rear.ROCKER_TERMINAL_LENGTH_MM
                - size[1] / 2,
                d.CASE_REAR_APERTURE_CENTER_Z_MM,
            ),
            0.2,
            collection,
        )
        obj.data.materials.append(palette["body"])
        obj["physical_reference"] = self.reference
        obj["fidelity"] = (
            "conservative receptacle envelope; supplier dimensions require confirmation"
        )
        return (obj,)
