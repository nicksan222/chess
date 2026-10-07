"""Concrete model instances, independent of the Blender runtime."""

from __future__ import annotations

from typing import TYPE_CHECKING

from shared import dimensions

if TYPE_CHECKING:
    import bpy


class Component:
    """One named physical instance; its concrete class builds its own geometry."""

    fit_check = False

    def __init__(self, reference: str) -> None:
        if not reference.strip():
            raise ValueError("component needs a reference")
        self.reference = reference

    @property
    def object_names(self) -> tuple[str, ...]:
        return (self.reference,)

    def build(
        self,
        collection: bpy.types.Collection,
        construction: bpy.types.Collection,
        palette: dict[str, bpy.types.Material],
    ) -> tuple[bpy.types.Object, ...]:
        raise NotImplementedError("concrete components must define their geometry")


class PrintableComponent(Component):
    """A component with one owning mesh and its inspection-view settings."""

    output_name: str = ""
    scene_name: str = ""
    volume_property: str = ""
    camera_location: tuple[float, float, float] = (0, 0, 0)
    camera_target: tuple[float, float, float] = (0, 0, 0)
    build_volume_mm = dimensions.REFERENCE_SERVICE_BUILD_VOLUME_MM
