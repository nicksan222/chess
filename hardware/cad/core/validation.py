"""Blender-side validation for generated prototype FDM parts."""

from collections.abc import Iterable
from typing import cast

import bmesh
import bpy

from core import dimensions as shared
from core import modeling


def validate_fdm_part(
    part: bpy.types.Object,
    build_volume_mm: tuple[float, float, float],
) -> None:
    """Require a positive, manifold mesh inside the selected print envelope."""
    mesh = modeling.require_object_data(part, bpy.types.Mesh)
    if mesh.validate(verbose=True):
        raise RuntimeError(f"Blender repaired invalid mesh data for {part.name}")

    dimensions = (
        float(part.dimensions.x),
        float(part.dimensions.y),
        float(part.dimensions.z),
    )
    if any(axis <= 0.0 for axis in dimensions):
        raise RuntimeError(f"{part.name} has a non-positive physical dimension")
    if not shared.fits_build_volume(dimensions, build_volume_mm):
        raise RuntimeError(
            f"{part.name} dimensions {dimensions} mm exceed the reference "
            f"build volume {build_volume_mm} mm"
        )

    bm = bmesh.new()
    bm.from_mesh(mesh)
    edges = cast(Iterable[bmesh.types.BMEdge], bm.edges)
    boundary_edges = sum(edge.is_boundary for edge in edges)
    non_manifold_edges = sum(not edge.is_manifold for edge in edges)
    volume = abs(bm.calc_volume(signed=True))
    bm.free()

    if boundary_edges != 0 or non_manifold_edges != 0:
        raise RuntimeError(
            f"{part.name} is not manifold: {boundary_edges} boundary and "
            f"{non_manifold_edges} non-manifold edges"
        )
    if volume <= 0.0:
        raise RuntimeError(f"{part.name} has no printable volume")

    part["intended_process"] = "Prototype FDM"
    part["bounding_box_x_mm"] = round(dimensions[0], 3)
    part["bounding_box_y_mm"] = round(dimensions[1], 3)
    part["bounding_box_z_mm"] = round(dimensions[2], 3)
    part["mesh_boundary_edges"] = boundary_edges
    part["mesh_non_manifold_edges"] = non_manifold_edges
    part["mesh_volume_mm3"] = round(volume, 2)
