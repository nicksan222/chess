"""Compose the generated case and plate into assembly views.

Presentation only. This project owns no printable geometry: it opens the case,
imports the plate exactly as generated, and adds a non-printed proxy for the
populated circuit board so a reader can see what fills the cavity.

Both parts are generated in assembly coordinates, so neither is moved here. If
the case and the plate ever stop meeting, that is a real dimension error rather
than a positioning mistake in this file.
"""

import sys
from dataclasses import dataclass
from pathlib import Path

import bpy
from mathutils import Vector

PROJECT_DIR = Path(__file__).parent
CAD_ROOT = PROJECT_DIR.parents[1]
sys.path.insert(0, str(CAD_ROOT))
GENERATED = CAD_ROOT / "generated"

from blocks import pcb_proxy
from core import dimensions as shared
from core import modeling, project

NAME = "board-assembly"

CASE_PART = "Printable_Board_Case"
PLATE_PART = "Printable_Tile_Plate"
EXPLODED_LIFT_MM = 70.0


@dataclass(frozen=True, slots=True)
class AssemblyMetadata:
    project_role: str
    case_source: str
    plate_source: str
    printable_geometry_redefined: bool
    printed_part_count: int
    square_count: int

    def apply_to(self, scene: bpy.types.Scene) -> None:
        project.set_scene_property(scene, "project_role", self.project_role)
        project.set_scene_property(scene, "case_source", self.case_source)
        project.set_scene_property(scene, "plate_source", self.plate_source)
        project.set_scene_property(
            scene,
            "printable_geometry_redefined",
            self.printable_geometry_redefined,
        )
        project.set_scene_property(scene, "printed_part_count", self.printed_part_count)
        project.set_scene_property(scene, "square_count", self.square_count)


def load_plate(plate_path: Path, collection: bpy.types.Collection) -> bpy.types.Object:
    """Import the plate exactly as its own generator produced it."""
    parts = modeling.load_objects(plate_path, (PLATE_PART,))
    plate = parts[PLATE_PART]
    if abs(plate.dimensions.x - shared.TILE_PLATE_SPAN_MM) > 0.01:
        raise RuntimeError(
            f"Plate source does not match shared dimensions: {plate.dimensions.x}"
        )
    collection.objects.link(plate)
    return plate


def render_views(
    plate: bpy.types.Object,
    electronics: bpy.types.Collection,
    output_directory: Path,
) -> None:
    scene = bpy.context.scene
    camera = modeling.require_object("Camera_Render")
    camera_data = modeling.require_object_data(camera, bpy.types.Camera)
    focus = Vector((0.0, shared.CASE_CENTER_OFFSET_Y_MM, 8.0))
    # The imported origin is already the assembled position, so it is the datum
    # the open view lifts away from rather than something to be overwritten.
    seated = plate.location.copy()

    # Closed: the finished board as a player sees it.
    plate.hide_render = False
    electronics.hide_render = True
    plate.location = seated
    camera.location = (340.0, -430.0, 330.0)
    camera_data.lens = 56
    modeling.point_at(camera, focus)
    scene.render.filepath = str(output_directory / f"{NAME}-finished.png")
    bpy.ops.render.render(write_still=True)

    # Open: the plate lifted clear, showing the board and the Pi beneath it.
    plate.location = seated + Vector((0.0, 0.0, EXPLODED_LIFT_MM))
    electronics.hide_render = False
    camera.location = (330.0, -450.0, 340.0)
    camera_data.lens = 52
    modeling.point_at(camera, focus + Vector((0.0, 0.0, 18.0)))
    scene.render.filepath = str(output_directory / f"{NAME}-open.png")
    bpy.ops.render.render(write_still=True)

    plate.location = seated


def build(output_directory: Path = GENERATED) -> None:
    case_path = output_directory / "board-case.blend"
    plate_path = output_directory / "tile-plate.blend"
    for source_path in (case_path, plate_path):
        if not source_path.is_file():
            raise RuntimeError(f"Generate element project first: {source_path}")

    bpy.ops.wm.open_mainfile(filepath=str(case_path))
    bpy.context.preferences.filepaths.save_version = 0
    scene = bpy.context.scene
    scene.name = "Single Board Assembly"
    project.apply_metadata(
        scene,
        AssemblyMetadata(
            project_role="Composite presentation only",
            case_source=str(Path("generated") / case_path.name),
            plate_source=str(Path("generated") / plate_path.name),
            printable_geometry_redefined=False,
            printed_part_count=2,
            square_count=shared.GRID_COUNT * shared.GRID_COUNT,
        ),
    )

    if CASE_PART not in bpy.data.objects:
        raise RuntimeError(f"{case_path} is missing {CASE_PART}")

    plate_collection = modeling.new_collection("PLATE_REFERENCE")
    electronics = modeling.new_collection("ELECTRONICS_REFERENCE")
    plate = load_plate(plate_path, plate_collection)
    pcb_proxy.add_board(electronics)

    output_path = output_directory / f"{NAME}.blend"
    bpy.ops.wm.save_as_mainfile(filepath=str(output_path))
    render_views(plate, electronics, output_directory)
    print(f"Saved {output_path}")


if __name__ == "__main__":
    build(project.output_directory(GENERATED))
