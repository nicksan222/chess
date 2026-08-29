"""Compose exact generated lid and tray sources into single-tile views."""

from math import pi
from pathlib import Path
import sys

import bpy
from mathutils import Vector


PROJECT_DIR = Path(__file__).parent
CAD_ROOT = PROJECT_DIR.parents[1]
sys.path.insert(0, str(CAD_ROOT))
GENERATED = CAD_ROOT / "generated"
GENERATED.mkdir(parents=True, exist_ok=True)

from core import dimensions as shared  # noqa: E402
from core import materials  # noqa: E402
from core import modeling  # noqa: E402
from core import presentation  # noqa: E402
from blocks import tile_electronics  # noqa: E402


TOP_PATH = GENERATED / "single-tile-top.blend"
BOTTOM_PATH = GENERATED / "single-tile-bottom.blend"
NAME = "single-tile-merged"
OUTPUT_PATH = GENERATED / f"{NAME}.blend"


def load_printable_sources(
    collection: bpy.types.Collection,
) -> tuple[bpy.types.Object, bpy.types.Object]:
    top = modeling.load_objects(TOP_PATH, ("Tile_Top_Lid",))["Tile_Top_Lid"]
    bottom = modeling.load_objects(BOTTOM_PATH, ("Tile_Bottom_Tray",))[
        "Tile_Bottom_Tray"
    ]
    collection.objects.link(top)
    collection.objects.link(bottom)
    for source in (top, bottom):
        if abs(source.dimensions.x - shared.TILE_SIZE_MM) > 0.01:
            raise RuntimeError(
                f"Generated source does not match shared tile size: {source.name}"
            )
    return top, bottom


def render_views(
    top: bpy.types.Object,
    bottom: bpy.types.Object,
    electronics: bpy.types.Collection,
) -> None:
    scene = bpy.context.scene
    camera = bpy.data.objects["Camera_Render"]

    camera.location = (48.0, -48.0, 52.0)
    camera.data.lens = 55
    modeling.point_at(camera, Vector((0.0, 0.0, 3.0)))
    scene.render.filepath = str(GENERATED / f"{NAME}.png")
    bpy.ops.render.render(write_still=True)

    top_location = top.location.copy()
    bottom_location = bottom.location.copy()
    top_rotation = top.rotation_euler.copy()
    top.location = (-24.0, 0.0, 4.5)
    top.rotation_euler[1] = pi
    bottom.location.x = 24.0
    camera.location = (72.0, -88.0, 72.0)
    camera.data.lens = 58
    modeling.point_at(camera, Vector((0.0, 0.0, 3.0)))
    scene.render.filepath = str(GENERATED / f"{NAME}-open.png")
    bpy.ops.render.render(write_still=True)
    top.location = top_location
    top.rotation_euler = top_rotation
    bottom.location = bottom_location

    electronics.hide_render = False
    top_location = top.location.copy()
    top_rotation = top.rotation_euler.copy()
    top.location = (-30.0, 7.0, 10.0)
    top.rotation_euler[1] = pi
    camera.location = (64.0, -76.0, 62.0)
    camera.data.lens = 58
    modeling.point_at(camera, Vector((-3.0, 0.0, 3.5)))
    scene.render.filepath = str(GENERATED / f"{NAME}-wired.png")
    bpy.ops.render.render(write_still=True)
    top.location = top_location
    top.rotation_euler = top_rotation
    electronics.hide_render = True


def build() -> None:
    for source_path in (TOP_PATH, BOTTOM_PATH):
        if not source_path.is_file():
            raise RuntimeError(f"Generate printable element first: {source_path}")

    modeling.clear_scene()
    scene = presentation.configure_scene(
        "Merged Universal Tile Presentation",
        shared.BLENDER_SCALE_LENGTH,
        (900, 900),
        (0.025, 0.03, 0.04, 1.0),
        0.35,
    )
    scene["project_role"] = "Imported printable sources and presentation references"
    scene["top_source"] = str(TOP_PATH.relative_to(CAD_ROOT))
    scene["bottom_source"] = str(BOTTOM_PATH.relative_to(CAD_ROOT))
    scene["printable_geometry_redefined"] = False
    scene["led_package_reference"] = shared.LED_PACKAGE_REFERENCE

    sources = modeling.new_collection("PRINTABLE_ELEMENT_REFERENCES")
    electronics = modeling.new_collection("WIRED_ELECTRONICS_REFERENCES")
    studio = modeling.new_collection("PRESENTATION")
    top, bottom = load_printable_sources(sources)
    tile_electronics.add_wired_electronics(electronics)
    electronics.hide_render = True

    floor_material = materials.solid(
        "Studio floor", (0.025, 0.028, 0.03, 1.0), 0.48
    )
    presentation.add_studio(
        studio,
        floor_material,
        (400.0, 400.0),
        (48.0, -48.0, 52.0),
        (0.0, 0.0, 3.0),
        55,
        presentation.TILE_STUDIO_LIGHTS,
    )

    bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT_PATH))
    render_views(top, bottom, electronics)
    print(f"Saved {OUTPUT_PATH}")


if __name__ == "__main__":
    build()
