"""Off-board plug housing envelope supplied by its PCB connector definition."""

from __future__ import annotations

import math
from typing import TYPE_CHECKING

from cad.harness.base.component import Component
from cad.harness.base.pcb import PcbPart
from shared import dimensions

if TYPE_CHECKING:
    import bpy


class ConnectorMate(Component):
    fit_check = True

    def __init__(self, connector: PcbPart) -> None:
        super().__init__(f"Mate_{connector.reference}")
        if not connector.mated_zones:
            raise ValueError("Connector must declare a mating envelope")
        self.connector = connector

    @property
    def object_names(self) -> tuple[str, ...]:
        return tuple(
            f"{self.reference}_{role}" for role in self.connector.mated_zone_roles
        )

    def build(
        self,
        collection: bpy.types.Collection,
        construction: bpy.types.Collection,
        palette: dict[str, bpy.types.Material],
    ) -> tuple[bpy.types.Object, ...]:
        from cad.harness.base.blender import modeling

        part = self.connector
        angle = math.radians(part.rotation_degrees)
        x, y = part.position_mm
        objects: list[bpy.types.Object] = []
        for zone, role in zip(part.mated_zones, part.mated_zone_roles, strict=True):
            start, end, width, height = zone
            mid = (start + end) / 2
            z = (
                dimensions.PCB_UNDERSIDE_Z_MM - height / 2
                if part.bottom
                else dimensions.PCB_TOP_Z_MM + height / 2
            )
            obj = modeling.rounded_box(
                f"{self.reference}_{role}",
                (width, end - start, height),
                (x + math.sin(angle) * mid, y - math.cos(angle) * mid, z),
                0,
                collection,
            )
            obj.rotation_euler.z = angle
            obj.data.materials.append(palette["body"])
            obj["fit_mates"] = [part.reference]
            obj["physical_reference"] = self.reference
            obj["mating_zone_role"] = role
            # The hidden wire-exit solid is a virtual dressing reservation, not
            # purchased housing. Only wires owned by this connector may occupy it.
            obj["reserved_connector"] = part.reference if role == "wire_exit" else ""
            obj.hide_render = role == "wire_exit"
            obj["fidelity"] = (
                "mating clearance envelope; no detailed latch/contact geometry"
            )
            objects.append(obj)
        return tuple(objects)
