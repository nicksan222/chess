"""Panel DC jack with bushing and supplied mounting-hardware envelopes."""

from __future__ import annotations

import math
from typing import TYPE_CHECKING

from cad.harness.base.component import Component
from shared import dimensions as d
from shared.dimensions.rear_panel import JACK_BODY_MM, REAR_PANEL_Y_MM

if TYPE_CHECKING:
    import bpy


class PanelDcJack(Component):
    fit_check = True
    product_key = "BARREL_JACK"

    def __init__(self) -> None:
        super().__init__(self.product_key)

    @property
    def object_names(self) -> tuple[str, ...]:
        return tuple(
            f"{self.reference}_{name}" for name in ("Body", "Bushing", "Washer", "Nut")
        )

    def build(
        self,
        collection: bpy.types.Collection,
        construction: bpy.types.Collection,
        palette: dict[str, bpy.types.Material],
    ) -> tuple[bpy.types.Object, ...]:
        from cad.harness.base.blender import modeling

        inside = REAR_PANEL_Y_MM - d.CASE_JACK_PANEL_THICKNESS_MM
        x, z = d.CASE_JACK_APERTURE_CENTER_X_MM, d.CASE_REAR_APERTURE_CENTER_Z_MM
        length, _, diameter = JACK_BODY_MM
        objects: list[bpy.types.Object] = []
        for name, outer, depth, y, bore in (
            ("Body", diameter, length, inside - length / 2, 5.5),
            (
                "Bushing",
                d.CASE_JACK_BUSHING_DIAMETER_MM,
                d.CASE_JACK_THREAD_LENGTH_MM,
                inside + d.CASE_JACK_THREAD_LENGTH_MM / 2,
                5.5,
            ),
            (
                "Washer",
                d.CASE_JACK_FLANGE_DIAMETER_MM,
                0.5,
                REAR_PANEL_Y_MM + 0.25,
                d.CASE_JACK_BUSHING_DIAMETER_MM,
            ),
            (
                "Nut",
                d.CASE_JACK_FLANGE_DIAMETER_MM,
                2.0,
                REAR_PANEL_Y_MM + 1.5,
                d.CASE_JACK_BUSHING_DIAMETER_MM,
            ),
        ):
            part = modeling.cylinder(
                f"{self.reference}_{name}",
                outer,
                depth,
                (x, y, z),
                collection,
                vertices=48 if name != "Nut" else 6,
            )
            part.rotation_euler.x = math.pi / 2
            cutter = modeling.cylinder(
                f"{name} socket bore",
                bore,
                depth + 1,
                (x, y, z),
                construction,
                vertices=48,
            )
            cutter.rotation_euler.x = math.pi / 2
            modeling.cut_batch(part, [cutter], "Socket bore")
            part.data.materials.append(palette["body"])
            part["physical_reference"] = self.reference
            part["fidelity"] = "dimension-based envelope; mounting hardware simplified"
            objects.append(part)
        return tuple(objects)
