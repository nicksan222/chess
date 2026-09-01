"""Compose the generated case and plate into assembly views.

Presentation only. This project owns no printable geometry: it opens the case,
imports the plate exactly as generated, and adds a non-printed proxy for the
populated circuit board so a reader can see what fills the cavity.

Both parts are generated in assembly coordinates, so neither is moved here. If
the case and the plate ever stop meeting, that is a real dimension error rather
than a positioning mistake in this file.
"""

import sys
from pathlib import Path

import bpy
from mathutils import Vector

PROJECT_DIR = Path(__file__).parent
CAD_ROOT = PROJECT_DIR.parents[1]
sys.path.insert(0, str(CAD_ROOT))
GENERATED = CAD_ROOT / "generated"
GENERATED.mkdir(parents=True, exist_ok=True)

from blocks import pcb_proxy
from core import dimensions as shared
from core import modeling

NAME = "board-assembly"
OUTPUT_PATH = GENERATED / f"{NAME}.blend"
CASE_PATH = GENERATED / "board-case.blend"
PLATE_PATH = GENERATED / "tile-plate.blend"

CASE_PART = "Printable_Board_Case"
PLATE_PART = "Printable_Tile_Plate"
EXPLODED_LIFT_MM = 70.0


def load_plate(collection: bpy.types.Collection) -> bpy.types.Object:
    """Import the plate exactly as its own generator produced it."""
    parts = modeling.load_objects(PLATE_PATH, (PLATE_PART,))
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
) -> None:
    scene = bpy.context.scene
    camera = bpy.data.objects["Camera_Render"]
    focus = Vector((0.0, shared.CASE_CENTER_OFFSET_Y_MM, 8.0))
    # The imported origin is already the assembled position, so it is the datum
    # the open view lifts away from rather than something to be overwritten.
    seated = plate.location.copy()

    # Closed: the finished board as a player sees it.
    plate.hide_render = False
    electronics.hide_render = True
    plate.location = seated
    camera.location = (340.0, -430.0, 330.0)
    camera.data.lens = 56
    modeling.point_at(camera, focus)
    scene.render.filepath = str(GENERATED / f"{NAME}-finished.png")
    bpy.ops.render.render(write_still=True)

    # Open: the plate lifted clear, showing the board and the Pi beneath it.
    plate.location = seated + Vector((0.0, 0.0, EXPLODED_LIFT_MM))
    electronics.hide_render = False
    camera.location = (330.0, -450.0, 340.0)
    camera.data.lens = 52
    modeling.point_at(camera, focus + Vector((0.0, 0.0, 18.0)))
    scene.render.filepath = str(GENERATED / f"{NAME}-open.png")
    bpy.ops.render.render(write_still=True)

    plate.location = seated


def build() -> None:
    for source_path in (CASE_PATH, PLATE_PATH):
        if not source_path.is_file():
            raise RuntimeError(f"Generate element project first: {source_path}")

    bpy.ops.wm.open_mainfile(filepath=str(CASE_PATH))
    bpy.context.preferences.filepaths.save_version = 0
    scene = bpy.context.scene
    scene.name = "Single Board Assembly"
    scene["project_role"] = "Composite presentation only"
    scene["case_source"] = str(CASE_PATH.relative_to(CAD_ROOT))
    scene["plate_source"] = str(PLATE_PATH.relative_to(CAD_ROOT))
    scene["printable_geometry_redefined"] = False
    scene["printed_part_count"] = 2
    scene["square_count"] = shared.GRID_COUNT * shared.GRID_COUNT

    if CASE_PART not in bpy.data.objects:
        raise RuntimeError(f"{CASE_PATH} is missing {CASE_PART}")

    plate_collection = modeling.new_collection("PLATE_REFERENCE")
    electronics = modeling.new_collection("ELECTRONICS_REFERENCE")
    plate = load_plate(plate_collection)
    pcb_proxy.add_board(electronics)

    bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT_PATH))
    render_views(plate, electronics)
    print(f"Saved {OUTPUT_PATH}")


if __name__ == "__main__":
    build()
