"""Render and validate registered mechanical components and their assembly."""

from collections.abc import Callable
from pathlib import Path
from typing import cast

import bpy
from mathutils import Vector

from cad.harness.base.blender import (
    materials,
    modeling,
    presentation,
    project,
    validation,
)
from cad.harness.base.component import Component, PrintableComponent
from shared import dimensions

FIT_NOISE_TOLERANCE_MM3 = 0.01


def fit_pair_exempt(first: bpy.types.Object, second: bpy.types.Object) -> bool:
    """Return whether two fit meshes share an explicitly declared interface."""
    a, b = first.get("physical_reference"), second.get("physical_reference")
    return bool(
        (bool(a) and a == b)
        or (
            not first.get("connector")
            and not second.get("connector")
            and (
                a in cast(list[str], second.get("fit_mates", []))
                or b in cast(list[str], first.get("fit_mates", []))
            )
        )
        or (
            # A connector's wires may occupy its virtual wire-exit reservation.
            # The visible housing has no reservation and still uses endpoint checks.
            first.get("reserved_connector")
            and first.get("reserved_connector") == second.get("connector")
        )
        or (
            second.get("reserved_connector")
            and second.get("reserved_connector") == first.get("connector")
        )
    )


def render_printable(part: PrintableComponent, output: Path) -> dict[str, object]:
    workspace = project.setup_printable(
        part.scene_name, dimensions.BLENDER_SCALE_LENGTH
    )
    objects = part.build(workspace.printable, workspace.construction, {})
    if len(objects) != 1 or objects[0].name != part.reference:
        raise RuntimeError(
            f"{part.reference}: printable component must own exactly one named mesh"
        )
    workspace.construction.hide_render = True
    workspace.construction.hide_viewport = True
    project.set_scene_property(workspace.scene, "design_status", "Printable prototype")
    project.set_scene_property(workspace.scene, "project_role", part.output_name)
    project.set_scene_property(workspace.scene, "grid_rows", dimensions.GRID_COUNT)
    project.set_scene_property(workspace.scene, "grid_columns", dimensions.GRID_COUNT)
    floor = materials.solid("Studio floor", (0.025, 0.028, 0.03, 1.0), 0.48)
    presentation.add_studio(
        workspace.studio,
        floor,
        (10_000, 10_000),
        part.camera_location,
        part.camera_target,
        56,
        presentation.BOARD_STUDIO_LIGHTS,
    )
    mesh = objects[0]
    project.save_printable(
        mesh, part.build_volume_mm, output, part.output_name, part.volume_property
    )
    return {
        "reference": part.reference,
        "dimensions_mm": [float(axis) for axis in mesh.dimensions],
        "volume_mm3": cast(float, mesh["mesh_volume_mm3"]),
        "boundary_edges": cast(int, mesh["mesh_boundary_edges"]),
        "non_manifold_edges": cast(int, mesh["mesh_non_manifold_edges"]),
    }


def render_assembly(
    case: PrintableComponent,
    plate_part: PrintableComponent,
    electronics: tuple[Component, ...],
    output: Path,
) -> dict[str, object]:
    """Import exact printable meshes, add electronics, and test their seated fit."""
    bpy.ops.wm.open_mainfile(filepath=str(output / f"{case.output_name}.blend"))
    scene = bpy.context.scene
    scene.name = "Single Board Assembly"
    scene["printed_part_count"] = 2 + sum(
        isinstance(part, PrintableComponent) for part in electronics
    )
    scene["printable_geometry_redefined"] = False
    scene["case_source"] = f"generated/{case.output_name}.blend"
    scene["plate_source"] = f"generated/{plate_part.output_name}.blend"
    plate_collection = modeling.new_collection("PLATE_REFERENCE")
    collection = modeling.new_collection("ELECTRONICS_REFERENCE")
    construction = modeling.new_collection("ELECTRONICS_CONSTRUCTION")
    plate = modeling.load_objects(
        output / f"{plate_part.output_name}.blend", (plate_part.reference,)
    )[plate_part.reference]
    plate_collection.objects.link(plate)
    if any(
        abs(a - b) > 0.01
        for a, b in zip(
            (plate.dimensions.x, plate.dimensions.y), dimensions.TILE_PLATE_SIZE_MM
        )
    ):
        raise RuntimeError("Plate source does not match its declared outline")
    case_mesh = modeling.require_object(case.reference)
    palette = {
        "pcb": materials.solid("Circuit board", (0.02, 0.16, 0.07, 1), 0.38),
        "body": materials.solid("Component body", (0.10, 0.10, 0.11, 1), 0.34),
        "emitter": materials.solid("RGB emitter window", (0.78, 0.86, 0.92, 1), 0.1),
        "host": materials.solid("Raspberry Pi board", (0.16, 0.05, 0.10, 1), 0.42),
        "display": materials.solid("OLED glass", (0.02, 0.02, 0.03, 1), 0.08),
    }
    fitted: list[bpy.types.Object] = []
    for part in electronics:
        if isinstance(part, PrintableComponent):
            obj = modeling.load_objects(
                output / f"{part.output_name}.blend", (part.reference,)
            )[part.reference]
            collection.objects.link(obj)
            objects = (obj,)
        else:
            objects = part.build(collection, construction, palette)
        if tuple(obj.name for obj in objects) != part.object_names:
            raise RuntimeError(
                f"{part.reference}: generated object names differ from its definition"
            )
        if part.fit_check:
            meshes = tuple(
                mesh
                for obj in objects
                for mesh in (obj, *obj.children_recursive)
                if mesh.type == "MESH" and mesh.get("fit_check", True)
            )
            for mesh in meshes:
                if mesh.get("source") != "chess-board.glb":
                    validation.weld_solid(mesh)
                mesh["physical_reference"] = mesh.get(
                    "physical_reference", mesh.get("pcb_reference", part.reference)
                )
            fitted.extend(meshes)
    construction.hide_render = True
    construction.hide_viewport = True
    checks = [
        (case_mesh, plate),
        *((printed, proxy) for printed in (case_mesh, plate) for proxy in fitted),
    ]
    # Check the imported PCB solids and off-board additions against one another,
    # allowing only same-component solids and declared mating interfaces.
    for first, second in validation.aabb_overlap_pairs(fitted):
        if fit_pair_exempt(first, second):
            continue
        checks.append((first, second))
    largest_overlap = 0.0
    for first, second in checks:
        if second.get("connector") and not first.get("connector"):
            first, second = second, first
        points: tuple[tuple[float, float, float], ...] = ()
        radius = 0.0
        if first.get("connector") and second.get("physical_reference") in cast(
            list[str], first.get("fit_mates", [])
        ):
            coordinates = cast(list[float], first["mating_points_mm"])
            points = (
                cast(tuple[float, float, float], tuple(coordinates[:3])),
                cast(tuple[float, float, float], tuple(coordinates[3:])),
            )
            radius = cast(float, first["mating_radius_mm"])
        volume = validation.overlap_volume_mm3(first, second, points, radius)
        largest_overlap = max(largest_overlap, volume)
        if volume > FIT_NOISE_TOLERANCE_MM3:
            raise RuntimeError(
                f"{first.name} and {second.name} overlap by {volume:.2f} mm3"
            )
    render_views(plate, collection, output)
    bpy.ops.wm.save_as_mainfile(filepath=str(output / "board-assembly.blend"))
    return {
        "fit_checks": len(checks),
        "largest_overlap_mm3": largest_overlap,
        "fit_noise_tolerance_mm3": FIT_NOISE_TOLERANCE_MM3,
        "interface_allowances": (
            "same physical reference and declared connector mating endpoints"
        ),
    }


def render_views(
    plate: bpy.types.Object,
    electronics: bpy.types.Collection,
    output: Path,
    render_still: Callable[[], object] | None = None,
) -> None:
    if render_still is None:
        render_still = lambda: bpy.ops.render.render(write_still=True)
    scene = bpy.context.scene
    camera = modeling.require_object("Camera_Render")
    camera_data = modeling.require_object_data(camera, bpy.types.Camera)
    fill = modeling.require_object("Fill_Light")
    fill_data = modeling.require_object_data(fill, bpy.types.AreaLight)
    focus = Vector((0, dimensions.CASE_CENTER_OFFSET_Y_MM, 8))
    seated = plate.location.copy()
    fill_energy = fill_data.energy

    def finished_view(render_path: str) -> None:
        plate.location = seated
        electronics.hide_render = False
        camera.location = (350, -450, 420)
        camera_data.lens = 36
        modeling.point_at(camera, focus)
        fill_data.energy = fill_energy
        scene.render.filepath = render_path
        bpy.context.view_layer.update()

    try:
        finished_view(str(output / "board-assembly-finished.png"))
        render_still()
        plate.location = seated + Vector((0, 0, 70))
        electronics.hide_render = False
        camera.location = (350, -460, 410)
        camera_data.lens = 34
        modeling.point_at(camera, focus + Vector((0, 0, 18)))
        fill_data.energy = fill_energy * 1.75
        scene.render.filepath = str(output / "board-assembly-open.png")
        render_still()
    finally:
        finished_view("//board-assembly-finished.png")
